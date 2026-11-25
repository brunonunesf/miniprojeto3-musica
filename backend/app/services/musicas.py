import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.musica import Musica
from app.schemas.musica import MusicaIn


def _normalizar(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.casefold().split())


def gerar_chave(dados: MusicaIn) -> str:
    return "|".join(_normalizar(c) for c in (dados.titulo, dados.artista, dados.versao))


def obter_ou_criar(db: Session, dados: MusicaIn) -> Musica:
    """Catálogo manual: reaproveita a música se a mesma gravação já foi cadastrada."""
    chave = gerar_chave(dados)
    musica = db.scalar(select(Musica).where(Musica.chave == chave))
    if musica:
        return musica

    musica = Musica(titulo=dados.titulo, artista=dados.artista, versao=dados.versao, chave=chave)
    db.add(musica)
    db.flush()  # gera o id; quem chamou decide o commit
    return musica
