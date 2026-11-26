from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.curtida import CurtidaOut
from app.schemas.ids import ID_MAXIMO
from app.services import curtidas as service

router = APIRouter(prefix="/posts", tags=["curtidas"])


@router.post("/{post_id}/curtir", response_model=CurtidaOut)
def curtir(
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.curtir(db, user, post_id)


@router.delete("/{post_id}/curtir", response_model=CurtidaOut)
def descurtir(
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.descurtir(db, user, post_id)
