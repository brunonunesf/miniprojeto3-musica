from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate


def criar(db: Session, autor: User, dados: PostCreate) -> Post:
    post = Post(texto=dados.texto, autor_id=autor.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def buscar(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post não encontrado")
    return post


def _buscar_do_autor(db: Session, post_id: int, user: User) -> Post:
    post = buscar(db, post_id)
    if post.autor_id != user.id:
        raise HTTPException(status_code=403, detail="só o autor pode alterar o post")
    return post


def atualizar(db: Session, post_id: int, user: User, dados: PostUpdate) -> Post:
    post = _buscar_do_autor(db, post_id, user)
    post.texto = dados.texto
    db.commit()
    db.refresh(post)
    return post


def excluir(db: Session, post_id: int, user: User) -> None:
    post = _buscar_do_autor(db, post_id, user)
    db.delete(post)
    db.commit()
