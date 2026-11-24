"""Catálogo fictício de demonstração; IDs estáveis pela chave curada."""
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.music import Music
from app.schemas.music import MusicData

CATALOGO = Path(__file__).resolve().parents[1] / "data" / "musicas.json"


def seed_musicas(db: Session, caminho: Path = CATALOGO) -> int:
    # Valida tudo antes de tocar no banco; duplicatas no arquivo são erro.
    dados = [MusicData.model_validate(item) for item in json.loads(caminho.read_text())]
    chaves = [m.chave_catalogo for m in dados]
    if len(set(chaves)) != len(chaves):
        raise ValueError("chave_catalogo repetida no catálogo")
    criadas = 0
    try:
        for item in dados:
            existente = db.scalar(select(Music).where(Music.chave_catalogo == item.chave_catalogo))
            if existente is None:
                db.add(Music(**item.model_dump()))
                criadas += 1
            else:
                for campo, valor in item.model_dump().items():
                    setattr(existente, campo, valor)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return criadas
