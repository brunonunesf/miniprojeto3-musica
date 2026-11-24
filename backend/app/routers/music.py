from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user
from app.schemas.music import MusicOut, MusicPage
from app.services import music as service

router = APIRouter(prefix="/musicas", tags=["musicas"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=MusicPage)
def listar(q: str = Query(default="", max_length=200),
           offset: int = Query(default=0, ge=0),
           limit: int = Query(default=20, ge=1, le=100),
           db: Session = Depends(get_db)):
    items, total = service.listar(db, q, offset, limit)
    return MusicPage(items=items, total=total, offset=offset, limit=limit)


@router.get("/{musica_id}", response_model=MusicOut)
def consultar(musica_id: int = Path(ge=1), db: Session = Depends(get_db)):
    return service.consultar(db, musica_id)
