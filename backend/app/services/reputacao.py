"""Liga o motor de reputação (core/reputacao.py, do Bruno) ao banco e à API.

A fonte de verdade são os eventos em `eventos_reputacao`. Os totais ficam em memória (no motor) e são
refeitos a partir dos eventos e da árvore quando o backend sobe. Cada fato é gravado junto com a
ação que o causou (mesmo commit) e só depois aplicado na memória, sob a trava da árvore.
"""

import logging

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.arvores import ErroArvore
from app.core.floresta import floresta
from app.core.reputacao import ErroReputacao, EventoCurtida, EventoDerivada, reputacao_reviews
from app.models.curtida import Curtida
from app.models.evento_reputacao import EventoReputacao
from app.models.post import Post
from app.services import arvores

log = logging.getLogger("uvicorn.error")

# Protegido por arvores.TRAVA; o banco continua sendo a fonte de verdade.
_disponivel = False


def disponivel() -> bool:
    with arvores.TRAVA:
        return _disponivel


def invalidar() -> None:
    """Oculta o snapshot antes de sincronizar uma alteração de origem confirmada."""
    global _disponivel
    with arvores.TRAVA:
        _disponivel = False


def _chave_curtida(usuario_id: int, review_id: int) -> str:
    return f"curtida:{usuario_id}:{review_id}"


def _chave_derivada(review_id: int) -> str:
    return f"derivada:{review_id}"


def evento_curtida(usuario_id: int, review_id: int) -> EventoReputacao:
    """A linha do evento, para quem curte gravá-la no mesmo commit da curtida."""
    return EventoReputacao(
        chave=_chave_curtida(usuario_id, review_id), tipo="curtida", review_id=review_id, usuario_id=usuario_id
    )


def evento_derivada(review_id: int) -> EventoReputacao:
    """A linha do evento, para quem cria a derivada gravá-la no mesmo commit da review."""
    return EventoReputacao(chave=_chave_derivada(review_id), tipo="derivada", review_id=review_id)


def _evento_do_motor(linha: EventoReputacao):
    if linha.tipo == "curtida":
        return EventoCurtida(linha.review_id, linha.usuario_id)
    if linha.tipo == "derivada":
        return EventoDerivada(linha.review_id)
    raise ErroReputacao("tipo de evento desconhecido")


def sincronizar_eventos(db: Session) -> int:
    """Cria os eventos que faltam para curtidas e derivadas que já existem (um seed, um banco antigo).

    Só acrescenta: nunca remove evento, porque os de reviews apagadas devem ser conservados.
    Repetir é seguro. Devolve quantos eventos novos foram criados.
    """
    existentes = set(db.scalars(select(EventoReputacao.chave)))
    novos = []
    for usuario_id, review_id in db.execute(select(Curtida.usuario_id, Curtida.post_id)):
        if _chave_curtida(usuario_id, review_id) not in existentes:
            novos.append(evento_curtida(usuario_id, review_id))
    for review_id in db.scalars(select(Post.id).where(Post.origem_id.is_not(None))):
        if _chave_derivada(review_id) not in existentes:
            novos.append(evento_derivada(review_id))
    if novos:
        db.add_all(novos)
        db.commit()
    return len(novos)


def reconstruir(db: Session) -> None:
    """Refaz os totais a partir dos eventos e da árvore. Levanta erro se algo estiver inconsistente."""
    global _disponivel
    with arvores.TRAVA:
        _disponivel = False
        linhas = db.scalars(select(EventoReputacao).order_by(EventoReputacao.id)).all()
        reputacao_reviews.reconstruir(floresta, [_evento_do_motor(linha) for linha in linhas])
        _disponivel = True


def tentar_reconstruir(db: Session) -> bool:
    """Como `reconstruir`, mas dado inconsistente vira aviso no log e não derruba quem chamou."""
    try:
        reconstruir(db)
        return True
    except (ErroArvore, ErroReputacao, SQLAlchemyError) as erro:
        db.rollback()
        log.warning("reputação não foi reconstruída: %s", erro)
        return False


def recalcular(db: Session) -> bool:
    """Reconstrói árvore e créditos do banco; falha deixa os totais indisponíveis.

    O(E) para os eventos e O(N) mais a ordenação da reconstrução da floresta.
    Não cria eventos. Nunca usa a floresta antiga se sua reconstrução falhar.
    """
    global _disponivel
    with arvores.TRAVA:
        _disponivel = False
        try:
            for _ in range(2):
                if not arvores.tentar_reconstruir(db):
                    return False
                if tentar_reconstruir(db):
                    return True
            return False
        except (ErroArvore, ErroReputacao, SQLAlchemyError) as erro:
            db.rollback()
            log.warning("reputação indisponível: %s", erro)
            return False


def garantir_disponibilidade(db: Session) -> bool:
    with arvores.TRAVA:
        return _disponivel or recalcular(db)


def aplicar_curtida(db: Session, usuario_id: int, review_id: int) -> None:
    _aplicar(db, EventoCurtida(review_id, usuario_id))


def aplicar_derivada(db: Session, review_id: int) -> None:
    _aplicar(db, EventoDerivada(review_id))


def _aplicar(db: Session, evento) -> None:
    """Põe o evento (já gravado) nos totais. Se a árvore em memória estava atrás do banco, refaz tudo."""
    with arvores.TRAVA:
        if not _disponivel:
            recalcular(db)  # inclui o evento já confirmado; não aplicar duas vezes
            return
        try:
            reputacao_reviews.aplicar(floresta, evento)
        except (ErroArvore, ErroReputacao):
            recalcular(db)


def remover_curtida(db: Session, usuario_id: int, review_id: int) -> None:
    """Desfaz exatamente os pontos que a curtida concedeu (descurtir)."""
    with arvores.TRAVA:
        if not _disponivel:
            recalcular(db)
            return
        reputacao_reviews.remover(EventoCurtida(review_id, usuario_id))


def apagar_evento_de_curtida(db: Session, usuario_id: int, review_id: int) -> None:
    db.execute(delete(EventoReputacao).where(EventoReputacao.chave == _chave_curtida(usuario_id, review_id)))


def total(db: Session, autor_id: int) -> int | None:
    """Os pontos de reputação de uma pessoa."""
    with arvores.TRAVA:
        if not garantir_disponibilidade(db):
            return None
        return reputacao_reviews.total(autor_id)
