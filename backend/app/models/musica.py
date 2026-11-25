from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Musica(Base):
    __tablename__ = "musicas"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    artista: Mapped[str] = mapped_column(String(200))
    versao: Mapped[str] = mapped_column(String(60), default="original")
    capa_url: Mapped[str] = mapped_column(String(300), default="")
    # título + artista + versão normalizados (sem acento nem maiúscula): identifica a gravação.
    chave: Mapped[str] = mapped_column(String(500), unique=True, index=True)
