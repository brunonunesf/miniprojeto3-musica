from typing import Literal, Self

from pydantic import BaseModel, model_validator

from app.schemas.post import PostOut

Visibilidade = Literal["privada", "publica"]


class ListaResumo(BaseModel):
    """Uma lista da biblioteca vista por quem pede. Lista restrita não revela nem a contagem."""

    visibilidade: Visibilidade
    acessivel: bool  # quem pede pode ver os itens (é a dona ou a lista é pública)
    total: int | None  # None quando a lista é restrita a quem pede


class BibliotecaOut(BaseModel):
    descobertas: ListaResumo  # músicas que a pessoa conheceu por outra review (review derivada)
    recomendacoes: ListaResumo  # músicas que a pessoa indicou por conta própria (review independente)


class BibliotecaUpdate(BaseModel):
    """Muda a visibilidade de uma ou das duas listas; o que não vier fica como está."""

    descobertas: Visibilidade | None = None
    recomendacoes: Visibilidade | None = None

    @model_validator(mode="after")
    def exigir_alguma_lista(self) -> Self:
        if self.descobertas is None and self.recomendacoes is None:
            raise ValueError("informe descobertas ou recomendacoes")
        return self


class BibliotecaPage(BaseModel):
    """Padrão de paginação do projeto. Cada item é uma review, no formato do feed, com a música e a origem."""

    lista: Literal["descobertas", "recomendacoes"]
    visibilidade: Visibilidade
    items: list[PostOut]
    total: int
    offset: int
    limit: int
