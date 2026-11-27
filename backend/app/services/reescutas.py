"""Reescutas: o aviso "ouvi novamente" (issue #12).

Um aviso é uma ação distinta de publicar uma review: **não cria review, nó da árvore, música nem pontos**, e a curtida
continua sendo uma só, na review original. Só o autor da review avisa que a ouviu de novo, com um comentário opcional,
e no máximo **uma vez por pessoa e música a cada 24 horas** (janela móvel, contada do aviso mais recente).
"""

import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import exists, func, insert, literal, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.follow import Follow
from app.models.post import Post
from app.models.reescuta import Reescuta
from app.models.user import User
from app.schemas.post import PostOut
from app.schemas.reescuta import ReescutaOut
from app.services import posts

JANELA = timedelta(hours=24)


def agora() -> datetime:
    """O relógio do servidor, em UTC. Os testes o trocam para andar no tempo sem esperar 24 horas."""
    return datetime.now(timezone.utc)


def _em_utc(momento: datetime) -> datetime:
    """O SQLite devolve datas sem fuso, e elas foram gravadas em UTC."""
    return momento if momento.tzinfo is not None else momento.replace(tzinfo=timezone.utc)


def registrar(db: Session, user: User, post_id: int, comentario: str) -> ReescutaOut:
    """Registra que a pessoa ouviu de novo a música da própria review.

    `403` se a review é de outra pessoa, `404` se não existe, `429` (com `Retry-After`) se já houve um aviso desta
    música nas últimas 24 horas. A checagem e a gravação são **um único comando** (`INSERT ... SELECT ... WHERE NOT
    EXISTS`), que o banco executa de uma vez: duas requisições simultâneas não passam as duas.
    """
    post = posts.buscar(db, post_id)
    if post.autor_id != user.id:
        raise HTTPException(status_code=403, detail="só o autor da review pode avisar que a ouviu de novo")

    momento = agora()
    ja_avisou = exists().where(
        Reescuta.autor_id == user.id, Reescuta.musica_id == post.musica_id, Reescuta.created_at > momento - JANELA
    )
    gravar = insert(Reescuta).from_select(
        ["autor_id", "musica_id", "post_id", "comentario", "created_at"],
        select(literal(user.id), literal(post.musica_id), literal(post.id), literal(comentario), literal(momento)).where(
            ~ja_avisou
        ),
    )
    try:
        gravadas = db.execute(gravar).rowcount
        if not gravadas:
            db.rollback()
            _recusar_por_janela(db, user.id, post.musica_id, momento)
        db.commit()
    except IntegrityError:
        # a review foi apagada entre a consulta e a gravação (a chave estrangeira recusou): 404
        db.rollback()
        posts.buscar(db, post_id)
        raise
    # (autor, música, data) é único: a janela de 24 horas impede dois avisos no mesmo instante
    aviso = db.scalars(
        select(Reescuta).where(Reescuta.autor_id == user.id, Reescuta.musica_id == post.musica_id, Reescuta.created_at == momento)
    ).one()
    return _montar(db, user, [aviso])[0]


def _recusar_por_janela(db: Session, autor_id: int, musica_id: int, momento: datetime):
    ultimo = db.scalar(
        select(func.max(Reescuta.created_at)).where(Reescuta.autor_id == autor_id, Reescuta.musica_id == musica_id)
    )
    segundos = 1
    if ultimo is not None:
        segundos = max(1, math.ceil((_em_utc(ultimo) + JANELA - momento).total_seconds()))
    horas, resto = divmod(segundos, 3600)
    quando = f"{horas} h e {resto // 60} min" if horas else f"{max(1, resto // 60)} min"
    raise HTTPException(
        status_code=429,
        detail=f"você já avisou que ouviu esta música de novo nas últimas 24 horas; tente de novo em {quando}",
        headers={"Retry-After": str(segundos)},
    )


def _montar(db: Session, user: User, avisos: list[Reescuta]) -> list[ReescutaOut]:
    """Os avisos com a review atual de cada um, no formato do feed e vista por quem pede, em poucas consultas."""
    if not avisos:
        return []
    reviews = {
        p.id: p
        for p in db.scalars(
            select(Post)
            .where(Post.id.in_({a.post_id for a in avisos}))
            .options(selectinload(Post.autor), selectinload(Post.musica))
        )
    }
    posts.anotar_interacoes(db, user, list(reviews.values()))
    return [
        ReescutaOut(id=a.id, comentario=a.comentario, created_at=a.created_at, review=PostOut.model_validate(reviews[a.post_id]))
        for a in avisos
        if a.post_id in reviews
    ]


def _pagina(db: Session, user: User, filtro, offset: int, limit: int) -> tuple[list[ReescutaOut], int]:
    total = db.scalar(select(func.count()).select_from(Reescuta).where(filtro)) or 0
    avisos = list(
        db.scalars(
            select(Reescuta)
            .where(filtro)
            # o id desempata avisos do mesmo instante, para a ordem ser estável
            .order_by(Reescuta.created_at.desc(), Reescuta.id.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    return _montar(db, user, avisos), total


def listar_da_review(db: Session, user: User, post_id: int, offset: int, limit: int) -> tuple[list[ReescutaOut], int]:
    """Os avisos de uma review (404 se ela não existe), do mais novo para o mais antigo."""
    posts.buscar(db, post_id)
    return _pagina(db, user, Reescuta.post_id == post_id, offset, limit)


def listar_do_feed(db: Session, user: User, offset: int, limit: int) -> tuple[list[ReescutaOut], int]:
    """Os avisos de quem a pessoa segue (sem os próprios), em ordem cronológica, para a tela intercalar com o feed."""
    seguidos = select(Follow.seguido_id).where(Follow.seguidor_id == user.id)
    return _pagina(db, user, Reescuta.autor_id.in_(seguidos), offset, limit)
