from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.user import User
from app.services import users


def seguir(db: Session, user: User, username: str) -> None:
    """Idempotente: seguir quem já se segue não muda nada."""
    alvo = users.buscar_por_username(db, username)
    if alvo.id == user.id:
        raise HTTPException(status_code=422, detail="você não pode seguir a si mesmo")

    db.add(Follow(seguidor_id=user.id, seguido_id=alvo.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # a relação já existia (a chave composta recusou a duplicata)


def deixar_de_seguir(db: Session, user: User, username: str) -> None:
    """Idempotente: deixar de seguir quem não se segue não é erro."""
    alvo = users.buscar_por_username(db, username)
    db.execute(delete(Follow).where(Follow.seguidor_id == user.id, Follow.seguido_id == alvo.id))
    db.commit()


def estatisticas(db: Session, quem_olha: User, perfil: User) -> dict:
    """Contadores do perfil e se quem olha já segue essa pessoa."""
    seguidores = db.scalar(select(func.count()).select_from(Follow).where(Follow.seguido_id == perfil.id))
    seguindo = db.scalar(select(func.count()).select_from(Follow).where(Follow.seguidor_id == perfil.id))
    eu_sigo = db.get(Follow, (quem_olha.id, perfil.id)) is not None
    return {"seguidores": seguidores or 0, "seguindo": seguindo or 0, "eu_sigo": eu_sigo}
