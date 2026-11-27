from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class VisibilidadeBiblioteca(Base):
    """Quem pode ver cada lista da biblioteca de uma pessoa (issue #12).

    As listas em si não são guardadas: saem das reviews da pessoa (as derivadas são as descobertas, as
    independentes são as recomendações). Só a visibilidade precisa de uma linha, e a linha só existe depois
    que a pessoa muda algo: sem linha valem os padrões, descobertas privadas e recomendações públicas.
    """

    __tablename__ = "visibilidades_biblioteca"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    descobertas_publicas: Mapped[bool] = mapped_column(default=False)
    recomendacoes_publicas: Mapped[bool] = mapped_column(default=True)
