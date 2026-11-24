from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class Music(Base):
    __tablename__ = "musicas"
    id: Mapped[int] = mapped_column(primary_key=True)
    chave_catalogo: Mapped[str] = mapped_column(String(100), unique=True)
    titulo: Mapped[str] = mapped_column(String(200))
    artista: Mapped[str] = mapped_column(String(200))
    tipo_versao: Mapped[str] = mapped_column(String(20))
    descricao_versao: Mapped[str] = mapped_column(String(200), default="")
    generos: Mapped[list[str]] = mapped_column(JSON)
    tags: Mapped[list[str]] = mapped_column(JSON)
