from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.ids import ID_MAXIMO
from app.schemas.catalogo_externo import BuscaOut, SolicitacaoCreate, SolicitacaoOut, SolicitacaoPage
from app.schemas.musica import MusicaOut, MusicaPage, MusicaPopularOut, MusicaPopularPage
from app.schemas.post import PostPage
from app.services import musicas as service

router = APIRouter(prefix="/musicas", tags=["musicas"])


@router.get("", response_model=MusicaPage)
def listar_musicas(
    q: str = Query(default="", max_length=200),
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.listar(db, q, offset, limit)
    return MusicaPage(items=items, total=total, offset=offset, limit=limit)


@router.get("/busca", response_model=BuscaOut)
async def buscar_em_todas_as_fontes(
    q: str = Query(default="", max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.catalogo_externo import buscar
    return await buscar(db, q.strip(), user.id)


@router.post("/solicitacoes", status_code=201, response_model=SolicitacaoOut)
def solicitar_inclusao(dados: SolicitacaoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.catalogo_externo import solicitar
    return solicitar(db, user.id, dados)


@router.get("/solicitacoes", response_model=SolicitacaoPage)
def minhas_solicitacoes(
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.models.catalogo_externo import SolicitacaoInclusao
    filtro = SolicitacaoInclusao.usuario_id == user.id
    total = db.scalar(select(func.count()).select_from(SolicitacaoInclusao).where(filtro))
    items = db.scalars(select(SolicitacaoInclusao).where(filtro).order_by(SolicitacaoInclusao.id.desc()).offset(offset).limit(limit))
    return {"items": [SolicitacaoOut.model_validate(p) for p in items], "total": total, "offset": offset, "limit": limit}


# A rota fixa vem antes da dinâmica: senão "populares" seria lido como o {musica_id}.
@router.get("/populares", response_model=MusicaPopularPage)
def listar_populares(
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    linhas, total = service.populares(db, offset, limit)
    items = [
        MusicaPopularOut(**MusicaOut.model_validate(musica).model_dump(), quantidade_reviews=quantidade)
        for musica, quantidade in linhas
    ]
    return MusicaPopularPage(items=items, total=total, offset=offset, limit=limit)


@router.get("/{musica_id}", response_model=MusicaOut)
def ver_musica(
    musica_id: int = Path(ge=1, le=ID_MAXIMO),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.consultar(db, musica_id)


@router.get("/{musica_id}/reviews", response_model=PostPage)
def listar_reviews_da_musica(
    musica_id: int = Path(ge=1, le=ID_MAXIMO),
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.reviews_da_musica(db, user, musica_id, offset, limit)
    return PostPage(items=items, total=total, offset=offset, limit=limit)
