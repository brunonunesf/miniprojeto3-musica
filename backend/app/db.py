import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# SQLite local, zero setup. O arquivo app.db NUNCA vai para o git (.gitignore).
# Os testes apontam DATABASE_URL para um banco descartável (ver tests/conftest.py).
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _ativar_chaves_estrangeiras(conexao, _registro):
    # O SQLite só confere chave estrangeira se pedirmos, e em cada conexão. Sem isto, uma curtida
    # ou um comentário podia ser gravado numa review apagada no meio do caminho.
    if engine.dialect.name == "sqlite":
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def atualizar_esquema_antigo() -> None:
    """Acrescenta as colunas que um `app.db` criado antes de uma entrega não tem.

    O `create_all` só cria tabelas que faltam e nunca altera as existentes. Sem isto, quem já tem
    banco local teria que apagá-lo ao puxar a branch. Só adiciona colunas novas e opcionais.
    """
    with engine.begin() as conexao:
        # A checagem e o ALTER usam a mesma conexão, para não depender de outra conexão do pool
        # que possa estar com o esquema desatualizado.
        colunas = {linha[1] for linha in conexao.execute(text("PRAGMA table_info(posts)"))}
        if not colunas or "origem_id" in colunas:  # sem tabela (banco novo) ou já atualizado
            return
        try:
            conexao.execute(text("ALTER TABLE posts ADD COLUMN origem_id INTEGER"))
        except OperationalError as erro:
            if "duplicate column" not in str(erro):  # já existe: o que se queria
                raise
        conexao.execute(text("CREATE INDEX IF NOT EXISTS ix_posts_origem_id ON posts (origem_id)"))


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
