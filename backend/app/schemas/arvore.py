from pydantic import BaseModel

from app.schemas.musica import MusicaOut


class AutorDoNo(BaseModel):
    username: str
    name: str


class NoArvore(BaseModel):
    """Uma review na árvore. Se foi apagada, o nó mantém o lugar e os ramos, mas sem autor nem nota."""

    id: int
    apagada: bool
    autor: AutorDoNo | None
    nota: int | None
    filhos: list["NoArvore"]


class ArvoreOut(BaseModel):
    musica: MusicaOut
    raiz: NoArvore
    # verdadeiro se a árvore tem mais reviews do que o limite de leitura (LIMITE_DA_ARVORE)
    truncada: bool
