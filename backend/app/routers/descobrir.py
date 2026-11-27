from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.descobrir import DescobrirPage
from app.schemas.ids import ID_MAXIMO
from app.services import descobrir as service

router = APIRouter(prefix="/descobrir", tags=["descobrir"])


@router.get("", response_model=DescobrirPage)
def ver_descobrir(
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total, personalizada = service.listar(db, user, offset, limit)
    return DescobrirPage(items=items, total=total, offset=offset, limit=limit, personalizada=personalizada)
