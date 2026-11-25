from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Follow(Base):
    """Quem segue quem. A chave composta garante uma relação só por par."""

    __tablename__ = "follows"

    seguidor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    seguido_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
