from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.musica import Musica
from catalogo_musical import carregar_catalogo


def importar_catalogo(db: Session) -> int:
    """Grava o catálogo curado no banco; repetir é seguro e preserva o id de cada chave.

    Devolve quantas músicas novas entraram. Um catálogo inválido levanta erro antes de gravar.
    """
    novas = 0
    for registro in carregar_catalogo():
        musica = db.scalar(select(Musica).where(Musica.chave_catalogo == registro["chave_catalogo"]))
        if musica is None:
            db.add(Musica(**registro))
            novas += 1
        else:
            for campo, valor in registro.items():
                setattr(musica, campo, valor)
    db.commit()
    return novas


def listar(db: Session, q: str, offset: int, limit: int) -> tuple[list[Musica], int]:
    # casefold em Python: o SQLite não compara maiúsculas e acentos de forma Unicode.
    # Custo O(n) por busca, aceitável para um catálogo curado pequeno.
    termos = q.casefold().split()
    musicas = list(db.scalars(select(Musica)))
    achadas = [m for m in musicas if all(t in f"{m.titulo} {m.artista}".casefold() for t in termos)]
    achadas.sort(key=lambda m: (m.titulo.casefold(), m.artista.casefold(), m.id))
    return achadas[offset : offset + limit], len(achadas)


def consultar(db: Session, musica_id: int) -> Musica:
    musica = db.get(Musica, musica_id)
    if not musica:
        raise HTTPException(status_code=404, detail="música não encontrada")
    return musica
