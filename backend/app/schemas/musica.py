from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Titulo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Versao = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class MusicaIn(BaseModel):
    titulo: Titulo
    artista: Titulo
    versao: Versao = "original"
    # endereço da imagem da capa; só http(s), como o avatar. Vazio = sem capa.
    capa_url: str = Field(default="", max_length=300, pattern=r"^(https?://\S+)?$")


class MusicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    artista: str
    versao: str
    capa_url: str
