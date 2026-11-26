from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.arvore import ArvoreOut
from app.schemas.ids import ID_MAXIMO
from app.services import arvores as service

router = APIRouter(prefix="/posts", tags=["arvores"])


@router.get("/{post_id}/arvore", response_model=ArvoreOut)
def ver_arvore(
    post_id: int = Path(ge=1, le=ID_MAXIMO),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.ler(db, post_id)
