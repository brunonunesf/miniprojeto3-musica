from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.comentario import Comentario
from app.models.curtida import Curtida
from app.models.musica import Musica
from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate
from app.services import users


def criar(db: Session, autor: User, dados: PostCreate) -> Post:
    musica = db.get(Musica, dados.musica_id)
    if not musica:
        raise HTTPException(status_code=422, detail="música não encontrada no catálogo")

    post = Post(texto=dados.texto, nota=dados.nota, autor_id=autor.id, musica_id=musica.id)
    db.add(post)
    try:
        db.commit()
    except IntegrityError:
        # a restrição única (autor, música) do banco decide, inclusive em envios simultâneos
        db.rollback()
        raise HTTPException(status_code=409, detail="você já fez uma review desta música")
    db.refresh(post)
    return post


def buscar(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post não encontrado")
    return post


def anotar_interacoes(db: Session, user: User, reviews: list[Post]) -> None:
    """Põe `curtidas`, `curtido_por_mim` e `comentarios` em cada review, com 3 consultas para a lista inteira."""
    if not reviews:
        return
    ids = [r.id for r in reviews]
    curtidas = dict(
        db.execute(
            select(Curtida.post_id, func.count()).where(Curtida.post_id.in_(ids)).group_by(Curtida.post_id)
        ).all()
    )
    minhas = set(
        db.scalars(select(Curtida.post_id).where(Curtida.usuario_id == user.id, Curtida.post_id.in_(ids)))
    )
    comentarios = dict(
        db.execute(
            select(Comentario.post_id, func.count()).where(Comentario.post_id.in_(ids)).group_by(Comentario.post_id)
        ).all()
    )
    for review in reviews:
        review.curtidas = curtidas.get(review.id, 0)
        review.curtido_por_mim = review.id in minhas
        review.comentarios = comentarios.get(review.id, 0)


def listar_reviews(db: Session, user: User, filtro, offset: int, limit: int) -> tuple[list[Post], int]:
    """Uma página de reviews que atendem ao `filtro`, da mais nova para a mais antiga.

    Serve ao feed, ao perfil e às reviews de uma música. O `total` conta o conjunto filtrado
    inteiro, antes da paginação.
    """
    total = db.scalar(select(func.count()).select_from(Post).where(filtro)) or 0
    reviews = list(
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
    anotar_interacoes(db, user, reviews)
    return reviews, total


def listar_do_usuario(db: Session, user: User, username: str, offset: int, limit: int) -> tuple[list[Post], int]:
    """As reviews de uma pessoa (404 se ela não existe), vistas por quem está logado."""
    autor = users.buscar_por_username(db, username)
    return listar_reviews(db, user, Post.autor_id == autor.id, offset, limit)


def detalhar(db: Session, user: User, post_id: int) -> Post:
    """A review com as curtidas vistas por quem está logado."""
    post = buscar(db, post_id)
    anotar_interacoes(db, user, [post])
    return post


def _buscar_do_autor(db: Session, post_id: int, user: User) -> Post:
    post = buscar(db, post_id)
    if post.autor_id != user.id:
        raise HTTPException(status_code=403, detail="só o autor pode alterar o post")
    return post


def atualizar(db: Session, post_id: int, user: User, dados: PostUpdate) -> Post:
    post = _buscar_do_autor(db, post_id, user)
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(post, campo, valor)
    db.commit()
    db.refresh(post)
    anotar_interacoes(db, user, [post])
    return post


def excluir(db: Session, post_id: int, user: User) -> None:
    post = _buscar_do_autor(db, post_id, user)
    # sem isto, curtidas e comentários ficariam órfãos e poderiam grudar numa review nova que reuse o id
    db.execute(delete(Curtida).where(Curtida.post_id == post.id))
    db.execute(delete(Comentario).where(Comentario.post_id == post.id))
    db.delete(post)
    db.commit()
