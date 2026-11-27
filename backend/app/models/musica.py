from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Musica(Base):
    """Uma gravação do catálogo curado (backend/data/musicas.json)."""

    __tablename__ = "musicas"

    id: Mapped[int] = mapped_column(primary_key=True)
    # identidade estável vinda do catálogo; o id do banco é atribuído aqui e preservado
    chave_catalogo: Mapped[str] = mapped_column(String(100), unique=True)
    titulo: Mapped[str] = mapped_column(String(200))
    artista: Mapped[str] = mapped_column(String(200))
    tipo_versao: Mapped[str] = mapped_column(String(20))
    descricao_versao: Mapped[str] = mapped_column(String(200), default="")
    generos: Mapped[list[str]] = mapped_column(JSON)
    tags: Mapped[list[str]] = mapped_column(JSON)
    # Sem capa usa texto vazio; mesmo limite de 2048 caracteres do catálogo.
    capa_url: Mapped[str] = mapped_column(String(2048), default="")

    curadoria_estado: Mapped[str] = mapped_column(String(20), default="curado", server_default="curado")
    curadoria_protegida: Mapped[bool] = mapped_column(default=False, server_default="0")
    incorporada_em: Mapped[int | None] = mapped_column(ForeignKey("musicas.id"), default=None)
