from datetime import datetime
from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
from app.models.user import User
from app.models.music import Music


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (Index("uq_review_ativa", "autor_id", "musica_id", unique=True,
                           sqlite_where=text("deleted_at IS NULL AND musica_id IS NOT NULL")),)
    id: Mapped[int] = mapped_column(primary_key=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    musica_id: Mapped[int | None] = mapped_column(ForeignKey("musicas.id"))
    texto: Mapped[str] = mapped_column(String(3000))
    created_at: Mapped[datetime] = mapped_column()
    edited_at: Mapped[datetime | None] = mapped_column()
    deleted_at: Mapped[datetime | None] = mapped_column()
    autor: Mapped[User] = relationship(lazy="joined")
    musica: Mapped[Music | None] = relationship(lazy="joined")
