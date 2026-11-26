from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.curtida import Curtida
from app.models.user import User
from app.schemas.curtida import CurtidaOut
from app.services import posts


def curtir(db: Session, user: User, post_id: int) -> CurtidaOut:
    """Idempotente: curtir de novo não duplica nem dá erro. Curtir a própria review é permitido."""
    posts.buscar(db, post_id)  # 404 se a review não existe
    db.add(Curtida(usuario_id=user.id, post_id=post_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Ou já estava curtida (a chave composta recusou a duplicata) ou a review foi apagada
        # entre a consulta e a gravação (a chave estrangeira recusou): neste caso, 404.
        posts.buscar(db, post_id)
    return estado(db, user, post_id)


def descurtir(db: Session, user: User, post_id: int) -> CurtidaOut:
    """Idempotente: descurtir o que não está curtido não é erro."""
    post = posts.buscar(db, post_id)
    db.execute(delete(Curtida).where(Curtida.usuario_id == user.id, Curtida.post_id == post.id))
    db.commit()
    return estado(db, user, post.id)


def estado(db: Session, user: User, post_id: int) -> CurtidaOut:
    total = db.scalar(select(func.count()).select_from(Curtida).where(Curtida.post_id == post_id))
    minha = db.get(Curtida, (user.id, post_id))
    return CurtidaOut(curtidas=total or 0, curtido_por_mim=minha is not None)
