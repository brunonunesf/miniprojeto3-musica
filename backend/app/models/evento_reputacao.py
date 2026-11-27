from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EventoReputacao(Base):
    """Um fato que gerou pontos: uma curtida ou a publicação de uma review derivada.

    É a fonte de verdade da reputação. Fica numa tabela própria, e não na de curtidas, porque apagar
    uma review apaga as curtidas dela, mas os créditos já concedidos são conservados (DECISIONS.md).
    Os totais não são guardados: são refeitos a partir daqui, e da árvore, quando o backend sobe.
    """

    __tablename__ = "eventos_reputacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    # "curtida:{usuario_id}:{review_id}" ou "derivada:{review_id}": um evento por fato, sem duplicata
    chave: Mapped[str] = mapped_column(String(80), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))
    # id da review, sem chave estrangeira: a review pode ter sido apagada e o id nunca é reaproveitado
    review_id: Mapped[int] = mapped_column(index=True)
    usuario_id: Mapped[int | None] = mapped_column(default=None)  # quem curtiu; vazio na derivada
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
