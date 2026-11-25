from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer
from app.schemas.music import MusicOut
from app.schemas.user import UserOut


class PostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texto: str = Field(min_length=1, max_length=3000)
    musica_id: int | None = Field(default=None, gt=0)

    @field_validator("texto", mode="before")
    @classmethod
    def limpar(cls, value):
        return value.strip() if isinstance(value, str) else value


class PostPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texto: str = Field(min_length=1, max_length=3000)
    limpar = field_validator("texto", mode="before")(PostCreate.limpar.__func__)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    texto: str
    autor: UserOut
    musica: MusicOut | None
    created_at: datetime
    edited_at: datetime | None

    @field_serializer("created_at", "edited_at")
    def datas_utc(self, value):
        return value.replace(tzinfo=timezone.utc).isoformat() if value else None


class PostPage(BaseModel):
    items: list[PostOut]
    total: int
    offset: int
    limit: int
