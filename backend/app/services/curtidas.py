from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.curtida import Curtida
from app.models.user import User
from app.schemas.curtida import CurtidaOut
from app.services import posts, reputacao


def curtir(db: Session, user: User, post_id: int) -> CurtidaOut:
    """Idempotente: curtir de novo não duplica nem dá erro. Curtir a própria review é permitido."""
    posts.buscar(db, post_id)  # 404 se a review não existe
    usuario_id = user.id
    db.add(Curtida(usuario_id=usuario_id, post_id=post_id))
    db.add(reputacao.evento_curtida(usuario_id, post_id))  # o fato que gera pontos, no mesmo commit
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Ou já estava curtida (a chave composta recusou a duplicata, e nada é pontuado de novo) ou a
        # review foi apagada entre a consulta e a gravação (a chave estrangeira recusou): neste caso, 404.
        posts.buscar(db, post_id)
    else:
        reputacao.aplicar_curtida(db, usuario_id, post_id)  # só curtida nova pontua
    return estado(db, user, post_id)


def descurtir(db: Session, user: User, post_id: int) -> CurtidaOut:
    """Idempotente: descurtir o que não está curtido não é erro."""
    post = posts.buscar(db, post_id)
    usuario_id = user.id
    removida = db.execute(
        delete(Curtida).where(Curtida.usuario_id == usuario_id, Curtida.post_id == post.id)
    ).rowcount
    if removida:
        reputacao.apagar_evento_de_curtida(db, usuario_id, post.id)  # descurtir retira os pontos
    db.commit()
    if removida:
        reputacao.remover_curtida(db, usuario_id, post.id)
    return estado(db, user, post.id)


def estado(db: Session, user: User, post_id: int) -> CurtidaOut:
    total = db.scalar(select(func.count()).select_from(Curtida).where(Curtida.post_id == post_id))
    minha = db.get(Curtida, (user.id, post_id))
    return CurtidaOut(curtidas=total or 0, curtido_por_mim=minha is not None)
