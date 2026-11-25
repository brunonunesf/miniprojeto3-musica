"""Orquestração transacional; adaptador de persistência é integração pendente."""
from typing import Protocol
from importlib import import_module
from importlib.util import find_spec

from sqlalchemy import Column, MetaData, String, Table, inspect, select
from cenarios_demo import preparar_cenario

metadata = MetaData()
cargas = Table('demo_seed_cargas', metadata, Column('versao', String(80), primary_key=True))


class IntegracaoPendente(RuntimeError):
    pass


class AdaptadorDemo(Protocol):
    def preparar_banco(self, engine) -> None:
        """Criar esquema oficial no banco temporário, incluindo migrações necessárias."""
    def validar(self, db, cenario) -> None:
        """Conferir carga inicial: contagens, identidades, origens e hashes/credenciais."""
    def verificar(self, db, cenario) -> None:
        """Somente leitura: validar modelos, capacidades e colisões; falhar antes de gravar."""
    def gravar(self, db, cenario, senha: str) -> None:
        """Gravar com flush, sem commit/rollback; usar hash e regras das áreas integradas."""


def seed_fake(db, adaptador: AdaptadorDemo | None = None):
    if db.new or db.dirty or db.deleted:
        raise ValueError('Seed exige sessão exclusiva sem mudanças pendentes')
    cenario = preparar_cenario()
    # Consultar a marca primeiro: reexecução não repõe itens removidos.
    if inspect(db.get_bind()).has_table(cargas.name):
        if db.scalar(select(cargas.c.versao).where(cargas.c.versao == cenario['versao'])):
            return 'já aplicada; ações preservadas'
    if adaptador is None:
        adaptador = carregar_adaptador()
    try:
        with db.no_autoflush:
            adaptador.verificar(db, cenario)
        cargas.create(db.connection(), checkfirst=True)
        adaptador.gravar(db, cenario, 'demo-trilha-13-2026')
        db.execute(cargas.insert().values(versao=cenario['versao']))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return 'carga aplicada'


def carregar_adaptador() -> AdaptadorDemo:
    """Ponto de integração proposto a Daniel; não presume esquema persistido."""
    modulo = 'app.services.demo_seed'
    if find_spec(modulo) is None:
        raise IntegracaoPendente(
            'Seed não aplicado: falta app.services.demo_seed.criar_adaptador() '
            'com modelos de músicas/posts (#3/#39), follows (#4), likes (#6) e origens (#10). '
            'Nenhum dado foi gravado. Valide a massa com --validar-demo.'
        )
    fabrica = getattr(import_module(modulo), 'criar_adaptador', None)
    if not callable(fabrica):
        raise IntegracaoPendente('Adaptador incompleto: falta fábrica criar_adaptador')
    adaptador = fabrica()
    for nome in ('verificar', 'gravar', 'preparar_banco', 'validar'):
        if not callable(getattr(adaptador, nome, None)):
            raise IntegracaoPendente(f'Adaptador incompleto: falta {nome}')
    return adaptador


def preparar_validar_banco(caminho, adaptador):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session

    engine = create_engine('sqlite:///' + str(caminho))
    @event.listens_for(engine, 'connect')
    def habilitar_fk(conexao, _):
        conexao.execute('PRAGMA foreign_keys=ON')
    try:
        adaptador.preparar_banco(engine)
        with Session(engine) as db:
            seed_fake(db, adaptador)
            adaptador.validar(db, preparar_cenario())
    finally:
        engine.dispose()
