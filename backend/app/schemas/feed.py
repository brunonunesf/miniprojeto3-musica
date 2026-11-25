from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, field_serializer
from app.schemas.post import PostOut


class FeedItem(PostOut):
    feed_id: str
    tipo: Literal["post", "republicacao"]
    feed_at: datetime
    comentario: str | None = None

    @field_serializer("feed_at")
    def data_feed(self, value):
        return value.replace(tzinfo=timezone.utc).isoformat()


class FeedPage(BaseModel):
    items: list[FeedItem]
    total: int
    offset: int
    limit: int
