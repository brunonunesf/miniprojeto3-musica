from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MusicData(BaseModel):
    chave_catalogo: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    titulo: str = Field(min_length=1, max_length=200)
    artista: str = Field(min_length=1, max_length=200)
    tipo_versao: Literal["original", "remix", "ao_vivo", "remaster"]
    descricao_versao: str = Field(default="", max_length=200)
    generos: list[str] = Field(min_length=1)
    tags: list[str] = Field(min_length=1)

    @field_validator("titulo", "artista", "descricao_versao", mode="before")
    @classmethod
    def limpar_texto(cls, value):
        return " ".join(value.split()) if isinstance(value, str) else value

    @field_validator("generos", "tags")
    @classmethod
    def limpar_termos(cls, values):
        termos = list(dict.fromkeys(" ".join(v.split()).casefold() for v in values))
        if any(not v or len(v) > 80 for v in termos):
            raise ValueError("termos devem ter de 1 a 80 caracteres")
        return termos


class MusicOut(MusicData):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MusicPage(BaseModel):
    items: list[MusicOut]
    total: int
    offset: int
    limit: int
