from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.post import Post
from app.models.user import User
from app.services.posts import listar_reviews


def listar(db: Session, user: User, offset: int, limit: int) -> tuple[list[Post], int]:
    """Reviews de quem a pessoa segue (sem as próprias), da mais nova para a mais antiga."""
    seguidos = select(Follow.seguido_id).where(Follow.seguidor_id == user.id)
    return listar_reviews(db, user, Post.autor_id.in_(seguidos), offset, limit)
