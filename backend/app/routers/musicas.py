from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.musica import MusicaOut, MusicaPage
from app.services import musicas as service

router = APIRouter(prefix="/musicas", tags=["musicas"])


@router.get("", response_model=MusicaPage)
def listar_musicas(
    q: str = Query(default="", max_length=200),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.listar(db, q, offset, limit)
    return MusicaPage(items=items, total=total, offset=offset, limit=limit)


@router.get("/{musica_id}", response_model=MusicaOut)
def ver_musica(
    musica_id: int = Path(ge=1),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.consultar(db, musica_id)
