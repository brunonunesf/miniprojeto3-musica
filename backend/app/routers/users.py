"""Slice de exemplo completo: model → schema → service → router → página Next.

Toda feature nova imita este caminho. 1 arquivo por router — registre o seu
com uma linha em main.py.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.contadores import contador_iniciais
from app.db import get_db
from app.schemas.user import UserCreate, UserOut, UserPage
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


from app.deps import get_current_user
from app.schemas.post import PostPage
from app.services import posts as posts_service


@router.get("/{username}/posts", response_model=PostPage, dependencies=[Depends(get_current_user)])
def posts_do_usuario(username: str, offset: int = Query(0, ge=0),
                     limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return posts_service.listar_autor(db, username, offset, limit)


from fastapi import Response
from app.models.user import User
from app.services import follows as follow_service


@router.get("/{username}/follow")
def estado_follow(username: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return follow_service.estado(db, username, user.id)


@router.post("/{username}/follow", status_code=204)
def seguir(username: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    follow_service.seguir(db, username, user.id, True)
    return Response(status_code=204)


@router.delete("/{username}/follow", status_code=204)
def deixar_de_seguir(username: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    follow_service.seguir(db, username, user.id, False)
    return Response(status_code=204)


@router.get("/{username}", dependencies=[Depends(get_current_user)])
def perfil_publico(username: str, db: Session = Depends(get_db)):
    return follow_service.perfil(db, username)
