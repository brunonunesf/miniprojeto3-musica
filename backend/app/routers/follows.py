from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services import follows as service

router = APIRouter(prefix="/usuarios", tags=["follows"])


@router.post("/{username}/follow", status_code=204)
def seguir(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.seguir(db, user, username)
    return Response(status_code=204)


@router.delete("/{username}/follow", status_code=204)
def deixar_de_seguir(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.deixar_de_seguir(db, user, username)
    return Response(status_code=204)
