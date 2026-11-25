from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.feed import FeedPage
from app.services import feed as service

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=FeedPage)
def listar(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.listar(db, user.id, offset, limit)
