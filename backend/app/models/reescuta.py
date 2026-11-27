from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Reescuta(Base):
    """O aviso "ouvi novamente" de uma pessoa sobre uma música que ela já avaliou (issue #12).

    Não é review, não entra na árvore e não pontua ninguém. Guarda a data e o comentário do aviso, e aponta para
    a review atual da pessoa (se a review for apagada, os avisos dela saem junto). O limite de um aviso por pessoa
    e música a cada 24 horas é imposto na gravação (services/reescutas.py), não por uma restrição de coluna,
    porque a janela é móvel.
    """

    # `sqlite_autoincrement`: o id de um aviso apagado não é reaproveitado.
    __table_args__ = (Index("ix_reescutas_autor_musica_data", "autor_id", "musica_id", "created_at"), {"sqlite_autoincrement": True})
    __tablename__ = "reescutas"

    id: Mapped[int] = mapped_column(primary_key=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    musica_id: Mapped[int] = mapped_column(ForeignKey("musicas.id"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    comentario: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)
