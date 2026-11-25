from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class RepublicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comentario: str = Field(default="", max_length=280)

    @field_validator("comentario", mode="before")
    @classmethod
    def limpar(cls, value):
        return value.strip() if isinstance(value, str) else value


class RepublicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    post_id: int
    autor_id: int
    comentario: str
    created_at: datetime

    @field_serializer("created_at")
    def data_utc(self, value):
        return value.replace(tzinfo=timezone.utc).isoformat()
