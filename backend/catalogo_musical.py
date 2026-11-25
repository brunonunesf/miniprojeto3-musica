"""Contrato de dados da #9, independente de app, banco e serviços externos."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, ValidationInfo, field_validator

CATALOGO_PADRAO = Path(__file__).resolve().parent / "data" / "musicas.json"


class MusicaCatalogo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chave_catalogo: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    titulo: str = Field(min_length=1, max_length=200)
    artista: str = Field(min_length=1, max_length=200)
    tipo_versao: Literal["original", "remix", "ao_vivo", "remaster"]
    descricao_versao: str = Field(max_length=200)
    generos: list[str] = Field(min_length=1)
    tags: list[str] = Field(min_length=1)
    capa_url: HttpUrl | None = Field(default=None, max_length=2048)

    @field_validator("titulo", "artista", "descricao_versao", mode="before")
    @classmethod
    def limpar_espacos(cls, valor):
        return " ".join(valor.split()) if isinstance(valor, str) else valor

    @field_validator("descricao_versao")
    @classmethod
    def identificar_versao(cls, valor: str, info: ValidationInfo):
        if info.data.get("tipo_versao") in {"remix", "ao_vivo", "remaster"} and not valor:
            raise ValueError("descrição obrigatória para versão não original")
        return valor

    @field_validator("generos", "tags")
    @classmethod
    def limpar_termos(cls, valores: list[str]):
        termos = list(dict.fromkeys(" ".join(valor.split()).casefold() for valor in valores))
        if any(not termo or len(termo) > 80 for termo in termos):
            raise ValueError("cada termo deve ter de 1 a 80 caracteres após a limpeza")
        return termos


class ErroCatalogo(ValueError):
    """Arquivo inválido; nenhum registro deve ser consumido parcialmente."""


def validar_catalogo(conteudo: object) -> list[dict]:
    """Valida o conjunto inteiro e devolve novas cópias normalizadas, sem gravar."""
    if not isinstance(conteudo, list) or not conteudo:
        raise ErroCatalogo("catálogo: esperado um array JSON com pelo menos uma entrada")

    erros: list[str] = []
    registros: list[dict] = []
    chaves: dict[str, int] = {}
    for indice, entrada in enumerate(conteudo, start=1):
        try:
            musica = MusicaCatalogo.model_validate(entrada)
        except ValidationError as exc:
            for erro in exc.errors():
                campo = ".".join(str(parte) for parte in erro["loc"]) or "registro"
                erros.append(f"entrada {indice}, campo {campo}: {erro['msg']}")
            continue
        if musica.chave_catalogo in chaves:
            erros.append(
                f"entrada {indice}, campo chave_catalogo: '{musica.chave_catalogo}' "
                f"repetida (primeira ocorrência na entrada {chaves[musica.chave_catalogo]})"
            )
        else:
            chaves[musica.chave_catalogo] = indice
        registros.append(musica.model_dump(mode="json"))

    if erros:
        raise ErroCatalogo("\n".join(erros))
    return registros


def carregar_catalogo(caminho: str | Path = CATALOGO_PADRAO) -> list[dict]:
    """Lê e valida tudo antes de retornar; não importa nem inicializa a aplicação."""
    caminho = Path(caminho)
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ErroCatalogo(f"{caminho}: JSON inválido na linha {exc.lineno}, coluna {exc.colno}") from exc
    except (OSError, UnicodeError) as exc:
        raise ErroCatalogo(f"{caminho}: não foi possível ler o catálogo UTF-8 ({exc})") from exc
    return validar_catalogo(conteudo)
