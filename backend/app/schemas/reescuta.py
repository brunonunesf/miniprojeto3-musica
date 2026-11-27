from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.post import PostOut

# strip antes de validar: o comentário é opcional, e só espaços valem como vazio.
Comentario = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class ReescutaCreate(BaseModel):
    comentario: Comentario = ""


class ReescutaOut(BaseModel):
    """Um aviso "ouvi novamente". A data e o comentário são os do aviso; a `review` é a de agora."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    comentario: str
    created_at: datetime
    review: PostOut  # a review atual da pessoa (se ela foi editada, aparece como está hoje); curtir é nela


class ReescutaPage(BaseModel):
    """Padrão de paginação do projeto, do aviso mais novo para o mais antigo."""

    items: list[ReescutaOut]
    total: int
    offset: int
    limit: int
