from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.follow import Follow
from app.models.post import Post
from app.models.user import User
from app.services.posts import anotar_curtidas


def listar(db: Session, user: User, offset: int, limit: int) -> tuple[list[Post], int]:
    """Reviews de quem a pessoa segue (sem as próprias), da mais nova para a mais antiga."""
    seguidos = select(Follow.seguido_id).where(Follow.seguidor_id == user.id)
    filtro = Post.autor_id.in_(seguidos)

    total = db.scalar(select(func.count()).select_from(Post).where(filtro)) or 0
    posts = list(
        db.scalars(
            select(Post)
            .where(filtro)
            # o id desempata reviews criadas no mesmo instante, para a ordem ser estável
            .order_by(Post.created_at.desc(), Post.id.desc())
            .offset(offset)
            .limit(limit)
            # carrega autor e música em lote: evita uma consulta extra por review
            .options(selectinload(Post.autor), selectinload(Post.musica))
        )
    )
    anotar_curtidas(db, user, posts)
    return posts, total
