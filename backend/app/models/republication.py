from datetime import datetime
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class Republication(Base):
    __tablename__ = "republicacoes"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column()
    comentario: Mapped[str] = mapped_column(String(280), default="")


class RepublicationWindow(Base):
    # Sobrevive à exclusão dos avisos para manter limite pessoa/música de 24h.
    __tablename__ = "republicacao_janelas"
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    musica_id: Mapped[int] = mapped_column(ForeignKey("musicas.id"), primary_key=True)
    last_at: Mapped[datetime] = mapped_column()
