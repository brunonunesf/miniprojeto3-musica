from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def agora():
    return datetime.now(timezone.utc)


class ReferenciaExterna(Base):
    __tablename__ = "referencias_externas"
    __table_args__ = (UniqueConstraint("servico", "id_externo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    musica_id: Mapped[int] = mapped_column(ForeignKey("musicas.id"), index=True)
    servico: Mapped[str] = mapped_column(String(10))
    id_externo: Mapped[str] = mapped_column(String(100))
    metadados: Mapped[dict] = mapped_column(JSON)
    isrc: Mapped[str] = mapped_column(String(12), index=True, default="")


class SolicitacaoInclusao(Base):
    __tablename__ = "solicitacoes_inclusao"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    artista: Mapped[str] = mapped_column(String(200))
    versao: Mapped[str] = mapped_column(String(200), default="")
    referencia: Mapped[str] = mapped_column(String(2048), default="")
    justificativa: Mapped[str] = mapped_column(String(1000), default="")
    estado: Mapped[str] = mapped_column(String(20), default="pendente")
    motivo: Mapped[str] = mapped_column(String(1000), default="")
    musica_id: Mapped[int | None] = mapped_column(ForeignKey("musicas.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(default=agora)


class RevisaoCorrespondencia(Base):
    __tablename__ = "revisoes_correspondencia"
    __table_args__ = (UniqueConstraint("musica_a", "musica_b"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    musica_a: Mapped[int] = mapped_column(ForeignKey("musicas.id"))
    musica_b: Mapped[int] = mapped_column(ForeignKey("musicas.id"))
    estado: Mapped[str] = mapped_column(String(20), default="pendente")


class AuditoriaCatalogo(Base):
    __tablename__ = "auditoria_catalogo"
    id: Mapped[int] = mapped_column(primary_key=True)
    autor: Mapped[str] = mapped_column(String(100))
    motivo: Mapped[str] = mapped_column(String(1000))
    acao: Mapped[str] = mapped_column(String(40))
    dados: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=agora)
