from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.comentario import Comentario
from app.models.user import User
from app.schemas.comentario import ComentarioCreate
from app.services import posts


def comentar(db: Session, autor: User, post_id: int, dados: ComentarioCreate) -> Comentario:
    post = posts.buscar(db, post_id)  # 404 se a review não existe
    comentario = Comentario(post_id=post.id, autor_id=autor.id, texto=dados.texto)
    db.add(comentario)
    db.commit()
    db.refresh(comentario)
    return comentario


def listar(db: Session, post_id: int, offset: int, limit: int) -> tuple[list[Comentario], int]:
    """Do mais antigo para o mais novo; o id desempata comentários do mesmo instante."""
    post = posts.buscar(db, post_id)
    total = db.scalar(select(func.count()).select_from(Comentario).where(Comentario.post_id == post.id)) or 0
    comentarios = list(
        db.scalars(
            select(Comentario)
            .where(Comentario.post_id == post.id)
            .order_by(Comentario.created_at, Comentario.id)
            .offset(offset)
            .limit(limit)
            .options(selectinload(Comentario.autor))
        )
    )
    return comentarios, total
