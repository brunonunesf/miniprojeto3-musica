from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.biblioteca import BibliotecaOut, BibliotecaPage, BibliotecaUpdate
from app.schemas.ids import ID_MAXIMO
from app.services import bibliotecas as service

router = APIRouter(prefix="/usuarios", tags=["bibliotecas"])


@router.patch("/eu/biblioteca", response_model=BibliotecaOut)
def mudar_visibilidade(
    dados: BibliotecaUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.atualizar(db, user, dados)


@router.get("/{username}/biblioteca", response_model=BibliotecaOut)
def ver_biblioteca(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.resumo(db, user, username)


@router.get("/{username}/biblioteca/{lista}", response_model=BibliotecaPage)
def ver_lista(
    username: str,
    lista: str,
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.listar(db, user, username, lista, offset, limit)
