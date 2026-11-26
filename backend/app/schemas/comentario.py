from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.user import UserOut

# strip antes de validar: "   " vira "" e é recusado.
TextoComentario = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ComentarioCreate(BaseModel):
    texto: TextoComentario


class ComentarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    texto: str
    autor: UserOut
    created_at: datetime


class ComentarioPage(BaseModel):
    items: list[ComentarioOut]
    total: int
    offset: int
    limit: int
