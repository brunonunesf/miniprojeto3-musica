from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.comentario import ComentarioCreate, ComentarioOut, ComentarioPage
from app.schemas.ids import ID_MAXIMO
from app.services import comentarios as service

router = APIRouter(prefix="/posts", tags=["comentarios"])


@router.post("/{post_id}/comentarios", response_model=ComentarioOut, status_code=201)
def comentar(
    dados: ComentarioCreate,
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.comentar(db, user, post_id, dados)


@router.get("/{post_id}/comentarios", response_model=ComentarioPage)
def listar_comentarios(
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=50, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.listar(db, post_id, offset, limit)
    return ComentarioPage(items=items, total=total, offset=offset, limit=limit)
