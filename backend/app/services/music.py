from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.music import Music


def listar(db: Session, q: str, offset: int, limit: int):
    # casefold em Python garante busca Unicode também no SQLite local.
    termos = " ".join(q.split()).casefold().split()
    musicas = list(db.scalars(select(Music).order_by(Music.id)))
    filtradas = [m for m in musicas if all(
        termo in f"{m.titulo} {m.artista}".casefold() for termo in termos
    )]
    filtradas.sort(key=lambda m: (m.titulo.casefold(), m.artista.casefold(), m.id))
    return filtradas[offset:offset + limit], len(filtradas)


def consultar(db: Session, musica_id: int):
    musica = db.get(Music, musica_id)
    if musica is None:
        raise HTTPException(status_code=404, detail="Música não encontrada")
    return musica
