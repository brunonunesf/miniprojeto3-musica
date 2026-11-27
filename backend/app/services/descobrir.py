"""Descobrir (#23): liga o recomendador TF-IDF (core/recomendador.py, do Bruno) ao banco.

O recomendador não conhece o banco: recebe o catálogo, as reviews e as curtidas e devolve o ranking
completo de músicas que a pessoa ainda não avaliou, uma review por música. Aqui ficam o snapshot, a
paginação (depois do ranking), a explicação em texto e o que não pode vazar para outra conta.

Privacidade: só as interações de quem pediu formam o perfil de gosto (o recomendador faz isso); as
curtidas das outras pessoas entram apenas na contagem que escolhe a review mais curtida de cada
música, e a resposta nunca traz perfil, score ou termos de outra conta.
"""

import logging
import threading
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.recomendador import Curtida as CurtidaRec
from app.core.recomendador import EntradaInvalida, Recomendador, Sugestao
from app.core.recomendador import Musica as MusicaRec
from app.core.recomendador import Review as ReviewRec
from app.models.curtida import Curtida
from app.models.musica import Musica
from app.models.post import Post
from app.models.user import User
from app.schemas.descobrir import SugestaoOut
from app.schemas.post import PostOut
from app.services import posts

log = logging.getLogger("uvicorn.error")

# O índice depende só do catálogo. Ele é refeito quando o catálogo muda (a assinatura abaixo muda),
# nunca editado no lugar: uma consulta em andamento continua com o índice que pegou.
_TRAVA = threading.Lock()
_indice: tuple[tuple, Recomendador] | None = None

_ROTULO_DO_TERMO = {"artista": "artista", "genero": "gênero", "tag": "tag"}


def _recomendador(musicas: list[Musica]) -> Recomendador:
    global _indice
    assinatura = tuple((m.chave_catalogo, m.artista, tuple(m.generos), tuple(m.tags)) for m in musicas)
    with _TRAVA:
        if _indice is None or _indice[0] != assinatura:
            catalogo = [MusicaRec(m.chave_catalogo, m.artista, tuple(m.generos), tuple(m.tags)) for m in musicas]
            _indice = (assinatura, Recomendador(catalogo))
        return _indice[1]


def _com_fuso(momento: datetime) -> datetime:
    """O SQLite devolve datas sem fuso, e elas foram gravadas em UTC."""
    return momento if momento.tzinfo is not None else momento.replace(tzinfo=timezone.utc)


def _snapshot(db: Session, chaves: dict[int, str]) -> tuple[list[ReviewRec], list[CurtidaRec]]:
    """Todas as reviews (só existem as ativas: apagar remove a linha) e as curtidas delas.

    As curtidas são filtradas pelas reviews lidas, porque uma review criada ou apagada entre as duas
    leituras deixaria uma curtida sem review e o recomendador recusaria o snapshot.
    """
    reviews = [
        ReviewRec(id=id_, musica=chaves[musica_id], autor=autor_id, data=_com_fuso(criada_em))
        for id_, musica_id, autor_id, criada_em in db.execute(
            select(Post.id, Post.musica_id, Post.autor_id, Post.created_at)
        )
    ]
    ids = {r.id for r in reviews}
    curtidas = [
        CurtidaRec(usuario=usuario_id, review=post_id)
        for usuario_id, post_id in db.execute(select(Curtida.usuario_id, Curtida.post_id))
        if post_id in ids
    ]
    return reviews, curtidas


def _termo_legivel(termo: str) -> str:
    campo, _, valor = termo.partition(":")
    return f"{_ROTULO_DO_TERMO.get(campo, campo)} {valor}"


def explicar(sugestao: Sugestao) -> str:
    """O motivo da sugestão. Só fala do que o algoritmo sabe: termos em comum, nunca acústica."""
    if sugestao.motivo == "afinidade":
        if not sugestao.caracteristicas:
            return "Combina com o que você avaliou ou curtiu."
        em_comum = ", ".join(_termo_legivel(t) for t in sugestao.caracteristicas)
        return f"Combina com o que você avaliou ou curtiu. Em comum: {em_comum}."
    if sugestao.motivo == "sem_afinidade":
        return "Não tem nada em comum com o que você avaliou ou curtiu, mas pode ser uma boa novidade."
    return "Você ainda não avaliou nem curtiu nada, então esta é uma review recente da comunidade."


def listar(db: Session, user: User, offset: int, limit: int) -> tuple[list[SugestaoOut], int, bool]:
    """Uma página de sugestões para quem está logado, o total do ranking e se ele é personalizado."""
    musicas = list(db.scalars(select(Musica).order_by(Musica.chave_catalogo)))
    recomendador = _recomendador(musicas)
    reviews, curtidas = _snapshot(db, {m.id: m.chave_catalogo for m in musicas})
    try:
        ranking = recomendador.recomendar(user.id, reviews, curtidas)
    except EntradaInvalida as erro:
        log.warning("Descobrir: snapshot recusado pelo recomendador: %s", erro)
        raise HTTPException(status_code=503, detail="não foi possível gerar sugestões agora")

    # a paginação é depois do ranking: a ordem é global e estável, e o total é o do ranking inteiro
    pagina = ranking[offset : offset + limit]
    carregadas = {
        p.id: p
        for p in db.scalars(
            select(Post)
            .where(Post.id.in_([s.review_id for s in pagina]))
            .options(selectinload(Post.autor), selectinload(Post.musica))
        )
    }
    # uma review apagada entre o snapshot e esta leitura simplesmente não aparece
    itens = [(carregadas[s.review_id], explicar(s)) for s in pagina if s.review_id in carregadas]
    posts.anotar_interacoes(db, user, [p for p, _ in itens])
    sugestoes = [SugestaoOut(review=PostOut.model_validate(p), explicacao=texto) for p, texto in itens]
    # sem sinais, todas as sugestões têm o motivo `sem_sinais`; com sinais, nenhuma tem
    personalizada = any(s.motivo != "sem_sinais" for s in ranking)
    return sugestoes, len(ranking), personalizada
