from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.comentario import Comentario
from app.models.user import User
from app.schemas.comentario import ComentarioCreate
from app.services import posts


def comentar(db: Session, autor: User, post_id: int, dados: ComentarioCreate) -> Comentario:
    posts.buscar(db, post_id)  # 404 se a review não existe
    comentario = Comentario(post_id=post_id, autor_id=autor.id, texto=dados.texto)
    db.add(comentario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # a review foi apagada entre a consulta e a gravação (a chave estrangeira recusou): 404
        posts.buscar(db, post_id)
        raise
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
