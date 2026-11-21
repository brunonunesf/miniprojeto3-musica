import secrets

import bcrypt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.contadores import contador_iniciais
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import LoginIn, RegistroIn


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def registrar(db: DbSession, dados: RegistroIn) -> User:
    ja_existe = db.scalar(select(User).where(User.username == dados.username))
    if ja_existe:
        raise HTTPException(status_code=409, detail="username já existe")

    user = User(
        username=dados.username,
        name=dados.name,
        password_hash=gerar_hash(dados.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    contador_iniciais.incrementar(user.username)
    return user


def logar(db: DbSession, dados: LoginIn) -> str:
    user = db.scalar(select(User).where(User.username == dados.username))
    if not user or not user.password_hash or not bcrypt.checkpw(
        dados.password.encode(), user.password_hash.encode()
    ):
        raise HTTPException(status_code=401, detail="usuário ou senha inválidos")

    token = secrets.token_urlsafe(32)
    db.add(Session(token=token, user_id=user.id))
    db.commit()
    return token
