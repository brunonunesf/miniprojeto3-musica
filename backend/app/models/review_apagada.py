from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ReviewApagada(Base):
    """O que sobra de uma review apagada: só o lugar dela na árvore, sem nota nem texto.

    O `id` é o da review original (nunca reaproveitado). As derivadas continuam apontando para
    ele e a pessoa que a escreveu mantém o crédito de origem (DECISIONS.md). Uma nova review da
    mesma pessoa e música é uma raiz nova, sem ligação com esta.
    """

    __tablename__ = "reviews_apagadas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    musica_id: Mapped[int] = mapped_column(ForeignKey("musicas.id"))
    origem_id: Mapped[int | None] = mapped_column(default=None)
    apagada_em: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
