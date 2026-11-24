from pydantic import BaseModel, Field, field_validator


class RegistroIn(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8)

    @field_validator("name", mode="before")
    @classmethod
    def limpar_nome(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def validar_senha(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("a senha deve ter no máximo 72 bytes UTF-8")
        return value


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    token: str
