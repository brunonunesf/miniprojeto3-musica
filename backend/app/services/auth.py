import secrets

import bcrypt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(User).where(User.username == dados.username)):
            raise HTTPException(status_code=409, detail="username já existe") from None
        raise
    db.refresh(user)

    contador_iniciais.incrementar(user.username)
    return user


def logar(db: DbSession, dados: LoginIn) -> str:
    user = db.scalar(select(User).where(User.username == dados.username))
    senha_valida = False
    if user and user.password_hash and len(dados.password.encode("utf-8")) <= 72:
        try:
            senha_valida = bcrypt.checkpw(
                dados.password.encode("utf-8"), user.password_hash.encode()
            )
        except ValueError:
            senha_valida = False
    if not senha_valida:
        raise HTTPException(status_code=401, detail="usuário ou senha inválidos")

    token = secrets.token_urlsafe(32)
    db.add(Session(token=token, user_id=user.id))
    db.commit()
    return token
