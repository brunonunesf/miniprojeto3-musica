from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.post import PostCreate, PostPatch, PostOut
from app.services import posts as service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostOut, status_code=201)
def criar(dados: PostCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.criar(db, dados, user.id)


@router.get("/{post_id}", response_model=PostOut)
def obter(post_id: int = Path(gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.obter(db, post_id)


@router.patch("/{post_id}", response_model=PostOut)
def editar(dados: PostPatch, post_id: int = Path(gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.editar(db, post_id, dados, user.id)


@router.delete("/{post_id}", status_code=204)
def excluir(post_id: int = Path(gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.excluir(db, post_id, user.id)
    return Response(status_code=204)
