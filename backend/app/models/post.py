from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.musica import Musica
from app.models.user import User


class Post(Base):
    """Uma review: nota de 0 a 10 para uma música, com texto opcional."""

    __tablename__ = "posts"
    # uma review por pessoa e música (DECISIONS.md)
    __table_args__ = (UniqueConstraint("autor_id", "musica_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    texto: Mapped[str] = mapped_column(String(5000), default="")
    nota: Mapped[int]
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    musica_id: Mapped[int] = mapped_column(ForeignKey("musicas.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), index=True
    )

    autor: Mapped[User] = relationship()
    musica: Mapped[Musica] = relationship()
