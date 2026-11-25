from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session
from app.models.follow import Follow
from app.models.user import User


def usuario(db: Session, username: str):
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise HTTPException(404, "Usuário não encontrado")
    return user


def perfil(db: Session, username: str):
    user = usuario(db, username)
    from app.schemas.user import UserOut
    return {**UserOut.model_validate(user).model_dump(),
            "seguidores": db.scalar(select(func.count()).select_from(Follow).where(Follow.seguido_id == user.id)) or 0,
            "seguindo": db.scalar(select(func.count()).select_from(Follow).where(Follow.seguidor_id == user.id)) or 0}


def estado(db: Session, username: str, autor_id: int):
    user = usuario(db, username)
    return {"seguindo": db.get(Follow, (autor_id, user.id)) is not None}


def seguir(db: Session, username: str, autor_id: int, ativo: bool):
    user = usuario(db, username)
    if user.id == autor_id:
        raise HTTPException(422, "Não é possível seguir a si mesmo")
    if ativo:
        db.execute(insert(Follow).values(seguidor_id=autor_id, seguido_id=user.id).on_conflict_do_nothing())
    else:
        db.execute(delete(Follow).where(Follow.seguidor_id == autor_id, Follow.seguido_id == user.id))
    db.commit()
