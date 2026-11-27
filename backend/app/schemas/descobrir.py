from pydantic import BaseModel

from app.schemas.post import PostOut


class SugestaoOut(BaseModel):
    """Uma review sugerida e o motivo, em texto para a pessoa ler."""

    review: PostOut
    explicacao: str


class DescobrirPage(BaseModel):
    """Padrão de paginação do projeto, mais `personalizada`.

    `personalizada` é falso enquanto a conta não tem reviews nem curtidas: nesse caso a lista é só
    um conjunto de reviews recentes da comunidade, não um ranking de afinidade.
    """

    items: list[SugestaoOut]
    total: int
    offset: int
    limit: int
    personalizada: bool
