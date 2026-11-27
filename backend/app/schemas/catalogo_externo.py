import re
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

Servico = Literal["spotify", "deezer"]
Versao = Literal["original", "ao_vivo", "remix", "remaster", "desconhecida"]


class FaixaExterna(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    servico: Servico
    id_externo: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9]+$")
    url: HttpUrl
    titulo: str = Field(min_length=1, max_length=200)
    artistas: list[str] = Field(min_length=1, max_length=30)
    album: str = Field(default="", max_length=200)
    duracao_ms: int | None = Field(default=None, gt=0, le=86400000)
    isrc: str = ""
    tipo_versao: Versao = "desconhecida"
    descricao_versao: str = Field(default="", max_length=200)
    capa_url: HttpUrl | None = None

    @field_validator("artistas")
    @classmethod
    def validar_artistas(cls, valores):
        if any(not a.strip() or len(a) > 200 for a in valores) or len(", ".join(valores)) > 200:
            raise ValueError("artistas inválidos")
        return [a.strip() for a in valores]

    @field_validator("isrc")
    @classmethod
    def normalizar_isrc(cls, valor):
        valor = valor.replace("-", "").strip().upper()
        if valor and not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{3}[0-9]{7}", valor):
            raise ValueError("ISRC inválido")
        return valor

    @model_validator(mode="after")
    def urls_validas(self) -> Self:
        host = "open.spotify.com" if self.servico == "spotify" else "www.deezer.com"
        if self.url.host not in (host, "deezer.com" if self.servico == "deezer" else host):
            raise ValueError("referência fora do serviço")
        if len(str(self.url)) > 2048 or (self.capa_url and len(str(self.capa_url)) > 2048):
            raise ValueError("URL muito longa")
        return self


class SolicitacaoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=200)
    artista: str = Field(min_length=1, max_length=200)
    versao: str = Field(default="", max_length=200)
    referencia: str = Field(default="", max_length=2048)
    justificativa: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def exigir_evidencia(self) -> Self:
        if not self.referencia and not self.justificativa:
            raise ValueError("informe uma referência ou justificativa")
        if self.referencia:
            from pydantic import TypeAdapter
            TypeAdapter(HttpUrl).validate_python(self.referencia)
        return self


class SolicitacaoOut(SolicitacaoCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estado: str
    motivo: str
    musica_id: int | None
    created_at: datetime


class MusicaPreview(BaseModel):
    titulo: str
    artista: str
    tipo_versao: Versao
    descricao_versao: str
    capa_url: str
    generos: list[str]
    tags: list[str]
    album: str = ""
    duracao_ms: int | None = None


class LinkFonte(BaseModel):
    servico: Servico
    url: HttpUrl


class ItemBusca(BaseModel):
    chave: str
    musica_id: int | None
    selecao_externa: str | None
    musica: MusicaPreview
    fontes: list[Literal["local", "spotify", "deezer"]]
    referencias: list[LinkFonte]


class BuscaOut(BaseModel):
    items: list[ItemBusca]
    total_local: int
    fontes: dict[str, str]


class SolicitacaoPage(BaseModel):
    items: list[SolicitacaoOut]
    total: int
    offset: int
    limit: int
