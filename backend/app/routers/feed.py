from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.ids import ID_MAXIMO
from app.schemas.post import PostPage
from app.services import feed as service

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=PostPage)
def ver_feed(
    offset: int = Query(default=0, ge=0, le=ID_MAXIMO),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.listar(db, user, offset, limit)
    return PostPage(items=items, total=total, offset=offset, limit=limit)
