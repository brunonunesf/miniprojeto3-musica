from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.ids import ID_MAXIMO
from app.schemas.reescuta import ReescutaCreate, ReescutaOut, ReescutaPage
from app.services import reescutas as service

router = APIRouter(tags=["reescutas"])


@router.post("/posts/{post_id}/reescutas", response_model=ReescutaOut, status_code=201)
def avisar_reescuta(
    dados: ReescutaCreate,
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.registrar(db, user, post_id, dados.comentario)


@router.get("/posts/{post_id}/reescutas", response_model=ReescutaPage)
def ver_reescutas_da_review(
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.listar_da_review(db, user, post_id, offset, limit)
    return ReescutaPage(items=items, total=total, offset=offset, limit=limit)


@router.get("/feed/reescutas", response_model=ReescutaPage)
def ver_reescutas_do_feed(
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.listar_do_feed(db, user, offset, limit)
    return ReescutaPage(items=items, total=total, offset=offset, limit=limit)
