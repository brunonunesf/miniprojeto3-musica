from sqlalchemy import String, case, func, literal, select, union_all
from sqlalchemy.orm import Session
from app.models.follow import Follow
from app.models.post import Post
from app.models.republication import Republication
from app.schemas.feed import FeedItem
from app.schemas.post import PostOut


def listar(db: Session, autor_id: int, offset: int, limit: int):
    seguidos = select(Follow.seguido_id).where(Follow.seguidor_id == autor_id)
    atividade = case((Post.musica_id.is_not(None), func.coalesce(Post.edited_at, Post.created_at)), else_=Post.created_at)
    publicacoes = select(literal("post").label("tipo"), Post.id.label("evento_id"),
                         Post.id.label("post_id"), atividade.label("data"),
                         literal(None, type_=String).label("comentario")).where(
                             Post.autor_id.in_(seguidos), Post.deleted_at.is_(None))
    avisos = select(literal("republicacao").label("tipo"), Republication.id.label("evento_id"),
                    Republication.post_id.label("post_id"), Republication.created_at.label("data"),
                    Republication.comentario.label("comentario")).join(Post, Post.id == Republication.post_id).where(
                        Republication.autor_id.in_(seguidos), Post.deleted_at.is_(None))
    eventos = union_all(publicacoes, avisos).subquery()
    total = db.scalar(select(func.count()).select_from(eventos)) or 0
    rows = db.execute(select(Post, eventos.c.tipo, eventos.c.evento_id, eventos.c.data, eventos.c.comentario)
                      .join(eventos, eventos.c.post_id == Post.id)
                      .order_by(eventos.c.data.desc(), eventos.c.tipo.desc(), eventos.c.evento_id.desc())
                      .offset(offset).limit(limit)).all()
    items = [FeedItem.model_validate({**PostOut.model_validate(post).model_dump(),
             "feed_id": f"{tipo}:{evento_id}", "tipo": tipo, "feed_at": data,
             "comentario": comentario}) for post, tipo, evento_id, data, comentario in rows]
    return {"items": items, "total": total, "offset": offset, "limit": limit}
