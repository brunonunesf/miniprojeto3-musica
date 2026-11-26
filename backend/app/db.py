import os

from sqlalchemy import create_engine, event, inspect, text
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
    inspetor = inspect(engine)
    if "posts" not in inspetor.get_table_names():
        return
    colunas = {coluna["name"] for coluna in inspetor.get_columns("posts")}
    if "origem_id" not in colunas:
        with engine.begin() as conexao:
            conexao.execute(text("ALTER TABLE posts ADD COLUMN origem_id INTEGER"))
            conexao.execute(text("CREATE INDEX IF NOT EXISTS ix_posts_origem_id ON posts (origem_id)"))


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
