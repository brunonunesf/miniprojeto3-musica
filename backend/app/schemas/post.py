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


class PostUpdate(BaseModel):
    # a música não muda na edição: trocá-la é decisão pendente (issue #9)
    nota: Nota | None = None
    texto: Texto | None = None

    @model_validator(mode="after")
    def exigir_algum_campo(self) -> Self:
        if self.nota is None and self.texto is None:
            raise ValueError("informe nota ou texto")
        return self


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    nota: int
    musica: MusicaOut
    autor: UserOut
    created_at: datetime
    # preenchidos por services.posts.anotar_curtidas; zero/falso se ninguém curtiu
    curtidas: int = 0
    curtido_por_mim: bool = False

    @computed_field
    @property
    def tem_texto(self) -> bool:
        """Indicador do feed: a review tem texto para abrir e ler."""
        return bool(self.texto)


class PostPage(BaseModel):
    """Padrão de paginação do projeto, para listas de reviews."""

    items: list[PostOut]
    total: int
    offset: int
    limit: int
