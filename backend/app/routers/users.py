"""Slice de exemplo completo: model → schema → service → router → página Next.

Toda feature nova imita este caminho. 1 arquivo por router — registre o seu
com uma linha em main.py.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.contadores import contador_iniciais
from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.ids import ID_MAXIMO
from app.schemas.post import PostPage
from app.schemas.user import PerfilOut, UserCreate, UserOut, UserPage, UserUpdate
from app.services import follows, posts, reputacao
from app.services import users as service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=UserPage)
def listar_usuarios(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    users, total = service.listar(db, offset, limit)
    return UserPage(items=users, total=total, offset=offset, limit=limit)


@router.get("/stats")
def stats_por_inicial():
    """Endpoint que USA a estrutura do core/ — alvo do teste-sabotagem de exemplo."""
    return {"usuarios_por_inicial": contador_iniciais.contagem()}


@router.post("", response_model=UserOut, status_code=201)
def criar_usuario(dados: UserCreate, db: Session = Depends(get_db)):
    # ponytail: criação sem senha — o guia de auth evolui isto para o registro real
    return service.criar(db, dados)


@router.patch("/eu", response_model=UserOut)
def editar_perfil(
    dados: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.atualizar(db, user, dados)


@router.get("/{username}", response_model=PerfilOut)
def ver_perfil(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    perfil = service.buscar_por_username(db, username)
    return PerfilOut(
        **UserOut.model_validate(perfil).model_dump(),
        **follows.estatisticas(db, user, perfil),
        reputacao=reputacao.total(db, perfil.id),
    )


@router.get("/{username}/posts", response_model=PostPage)
def ver_reviews_do_usuario(
    username: str,
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = posts.listar_do_usuario(db, user, username, offset, limit)
    return PostPage(items=items, total=total, offset=offset, limit=limit)
