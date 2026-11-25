from sqlalchemy import case, func, select
from sqlalchemy.orm import Session
from app.models.follow import Follow
from app.models.post import Post
from app.schemas.feed import FeedItem
from app.schemas.post import PostOut


def listar(db: Session, autor_id: int, offset: int, limit: int):
    seguidos = select(Follow.seguido_id).where(Follow.seguidor_id == autor_id)
    filtro = (Post.autor_id.in_(seguidos), Post.deleted_at.is_(None))
    atividade = case((Post.musica_id.is_not(None), func.coalesce(Post.edited_at, Post.created_at)), else_=Post.created_at)
    total = db.scalar(select(func.count()).select_from(Post).where(*filtro)) or 0
    rows = db.execute(select(Post, atividade.label("atividade")).where(*filtro)
                      .order_by(atividade.desc(), Post.id.desc()).offset(offset).limit(limit)).all()
    items = [FeedItem.model_validate({**PostOut.model_validate(post).model_dump(),
             "feed_id": f"post:{post.id}", "tipo": "post", "feed_at": data}) for post, data in rows]
    return {"items": items, "total": total, "offset": offset, "limit": limit}
