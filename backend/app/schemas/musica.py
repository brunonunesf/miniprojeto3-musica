from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Titulo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Versao = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class MusicaIn(BaseModel):
    titulo: Titulo
    artista: Titulo
    versao: Versao = "original"


class MusicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    artista: str
    versao: str
