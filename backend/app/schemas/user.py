from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

# Colidem com rotas fixas de /usuarios: o perfil dessas contas ficaria inacessível.
NOMES_RESERVADOS = {"eu", "stats"}


def recusar_nome_reservado(username: str) -> str:
    if username in NOMES_RESERVADOS:
        raise ValueError("esse username é reservado")
    return username


Username = Annotated[
    str,
    Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$"),
    AfterValidator(recusar_nome_reservado),
]


class UserCreate(BaseModel):
    username: Username
    name: str = Field(min_length=1, max_length=80)
    bio: str = Field(default="", max_length=280)
    avatar_url: str = Field(default="", max_length=300)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    bio: str | None = Field(default=None, max_length=280)
    avatar_url: str | None = Field(default=None, max_length=300, pattern=r"^(https?://\S+)?$")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    bio: str
    avatar_url: str
    created_at: datetime


class PerfilOut(UserOut):
    """O perfil de alguém visto por quem está logado."""

    seguidores: int
    seguindo: int
    eu_sigo: bool  # quem olha já segue esta pessoa (estado do botão de seguir)


class UserPage(BaseModel):
    """Padrão de paginação do projeto: todo endpoint de listagem devolve isto."""

    items: list[UserOut]
    total: int
    offset: int
    limit: int
