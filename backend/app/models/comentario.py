from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.user import User


class Comentario(Base):
    """Comentário plano numa review: não tem resposta nem pontua ninguém."""

    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    texto: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    autor: Mapped[User] = relationship()
