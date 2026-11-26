from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.ids import ID_MAXIMO
from app.schemas.post import PostCreate, PostOut, PostUpdate
from app.services import posts as service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostOut, status_code=201)
def criar_post(
    dados: PostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.criar(db, user, dados)


@router.get("/{post_id}", response_model=PostOut)
def ver_post(
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.buscar(db, post_id)


@router.patch("/{post_id}", response_model=PostOut)
def editar_post(
    dados: PostUpdate,
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.atualizar(db, post_id, user, dados)


@router.delete("/{post_id}", status_code=204)
def excluir_post(
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.excluir(db, post_id, user)
    return Response(status_code=204)
