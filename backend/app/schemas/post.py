from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.user import UserOut

# strip antes de validar: "   " vira "" e é recusado (min_length=1).
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class PostCreate(BaseModel):
    texto: Texto


class PostUpdate(BaseModel):
    texto: Texto


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    autor: UserOut
    created_at: datetime
