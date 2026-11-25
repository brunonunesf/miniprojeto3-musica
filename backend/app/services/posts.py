from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.post import Post
from app.models.republication import Republication
from app.models.music import Music
from app.models.user import User


def agora():
    # SQLite guarda UTC sem timezone; schemas serializam explicitamente em UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def escrita(db: Session):
    # Serializa decisão+gravação entre conexões/processos no SQLite do projeto.
    # Precisa ocorrer antes de ler a review, inclusive em edição/exclusão.
    db.execute(text("BEGIN IMMEDIATE"))


def obter(db: Session, post_id: int):
    post = db.scalar(select(Post).where(Post.id == post_id, Post.deleted_at.is_(None)))
    if post is None:
        raise HTTPException(404, "Publicação não encontrada ou apagada")
    return post


def proprio(db: Session, post_id: int, autor_id: int):
    post = obter(db, post_id)
    if post.autor_id != autor_id:
        raise HTTPException(403, "Somente o autor pode alterar esta publicação")
    return post


def criar(db: Session, dados, autor_id: int):
    escrita(db)
    if dados.musica_id is not None and db.get(Music, dados.musica_id) is None:
        raise HTTPException(422, "Música não encontrada")
    post = Post(**dados.model_dump(), autor_id=autor_id, created_at=agora())
    db.add(post)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existente = db.scalar(select(Post).where(Post.autor_id == autor_id,
            Post.musica_id == dados.musica_id, Post.deleted_at.is_(None)))
        if existente is None:
            raise
        raise HTTPException(409, {"message": "Você já tem uma review desta versão. Quer editar ou republicar?",
                                  "post_id": existente.id})
    db.refresh(post)
    return post


def editar(db: Session, post_id: int, dados, autor_id: int):
    escrita(db)
    post = proprio(db, post_id, autor_id)
    if post.texto != dados.texto:
        post.texto = dados.texto
        post.edited_at = agora()
    db.commit()
    db.refresh(post)
    return post


def excluir(db: Session, post_id: int, autor_id: int):
    escrita(db)
    post = proprio(db, post_id, autor_id)
    db.execute(delete(Republication).where(Republication.post_id == post.id))
    post.texto = ""
    post.deleted_at = agora()
    db.commit()


def listar_autor(db: Session, username: str, offset: int, limit: int):
    autor = db.scalar(select(User).where(User.username == username))
    if autor is None:
        raise HTTPException(404, "Usuário não encontrado")
    filtro = (Post.autor_id == autor.id, Post.deleted_at.is_(None))
    total = db.scalar(select(func.count()).select_from(Post).where(*filtro)) or 0
    items = list(db.scalars(select(Post).where(*filtro).order_by(Post.created_at.desc(), Post.id.desc()).offset(offset).limit(limit)))
    return {"items": items, "total": total, "offset": offset, "limit": limit}
