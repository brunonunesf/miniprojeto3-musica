"""Orquestração transacional; adaptador de persistência é integração pendente."""
from typing import Protocol

from sqlalchemy import Column, MetaData, String, Table, inspect, select
from cenarios_demo import preparar_cenario

metadata = MetaData()
cargas = Table('demo_seed_cargas', metadata, Column('versao', String(80), primary_key=True))


class IntegracaoPendente(RuntimeError):
    pass


class AdaptadorDemo(Protocol):
    def verificar(self, db, cenario) -> None:
        """Somente leitura: validar modelos, capacidades e colisões; falhar antes de gravar."""
    def gravar(self, db, cenario, senha: str) -> None:
        """Gravar com flush, sem commit/rollback; usar hash e regras das áreas integradas."""


def seed_fake(db, adaptador: AdaptadorDemo | None = None):
    cenario = preparar_cenario()
    # Consultar a marca primeiro: reexecução não repõe itens removidos.
    if inspect(db.get_bind()).has_table(cargas.name):
        if db.scalar(select(cargas.c.versao).where(cargas.c.versao == cenario['versao'])):
            return 'já aplicada; ações preservadas'
    if adaptador is None:
        raise IntegracaoPendente(
            'Seed não aplicado: falta adaptador aprovado com Daniel para músicas/posts (#3), '
            'follows (#4), likes (#6), árvores e eventos (#10), e catálogo (#39). '
            'Nenhum dado foi gravado. Valide a massa com --validar-demo.'
        )
    adaptador.verificar(db, cenario)
    try:
        cargas.create(db.connection(), checkfirst=True)
        adaptador.gravar(db, cenario, 'demo-trilha-13-2026')
        db.execute(cargas.insert().values(versao=cenario['versao']))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return 'carga aplicada'
