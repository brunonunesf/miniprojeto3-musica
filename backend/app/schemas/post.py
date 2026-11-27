from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field, model_validator

from app.schemas.ids import ID_MAXIMO
from app.schemas.musica import MusicaOut
from app.schemas.user import UserOut

# strip antes de validar. O texto é opcional: uma review pode ter só a nota.
Texto = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]
Nota = Annotated[int, Field(ge=0, le=10)]


class PostCreate(BaseModel):
    musica_id: int = Field(ge=1, le=ID_MAXIMO)  # escolhida no catálogo (GET /musicas)
    nota: Nota
    texto: Texto = ""
    # Review de onde esta partiu: faz desta uma review derivada. Precisa ser da mesma música.
    origem_id: int | None = Field(default=None, ge=1, le=ID_MAXIMO)

    @model_validator(mode="after")
    def derivada_exige_texto(self) -> Self:
        if self.origem_id is not None and not self.texto:
            raise ValueError("a review derivada precisa de texto próprio")
        return self


class OrigemUpdate(BaseModel):
    """Corrigir de onde uma review derivada partiu: só troca uma origem por outra."""

    origem_id: int = Field(ge=1, le=ID_MAXIMO)


class PostUpdate(BaseModel):
    # a música não muda na edição: trocá-la é decisão pendente (issue #9)
    nota: Nota | None = None
    texto: Texto | None = None

    @model_validator(mode="after")
    def exigir_algum_campo(self) -> Self:
        if self.nota is None and self.texto is None:
            raise ValueError("informe nota ou texto")
        return self


class OrigemOut(BaseModel):
    """A review de onde uma derivada partiu (só quando ela ainda existe)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    autor: UserOut


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    nota: int
    musica: MusicaOut
    autor: UserOut
    created_at: datetime
    # `origem_id` aparece em toda derivada. `origem` só se a review de origem ainda existe: se ela
    # foi apagada fica vazio, e a árvore (`GET /posts/{id}/arvore`) mostra o lugar dela.
    origem_id: int | None = None
    origem: OrigemOut | None = None
    # preenchidos por services.posts.anotar_interacoes; zero/falso se não há interações
    curtidas: int = 0
    curtido_por_mim: bool = False
    comentarios: int = 0

    @computed_field
    @property
    def tem_texto(self) -> bool:
        """Indicador do feed: a review tem texto para abrir e ler."""
        return bool(self.texto)


class OrigemCorrigidaOut(PostOut):
    reputacao_disponivel: bool


class PostPage(BaseModel):
    """Padrão de paginação do projeto, para listas de reviews."""

    items: list[PostOut]
    total: int
    offset: int
    limit: int
