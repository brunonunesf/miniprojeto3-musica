import math
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.republication import Republication, RepublicationWindow
from app.services import posts


def criar(db: Session, post_id: int, dados, autor_id: int):
    posts.escrita(db)
    post = posts.proprio(db, post_id, autor_id)
    if post.musica_id is None:
        raise HTTPException(422, "Somente reviews musicais podem ser republicadas")
    agora = posts.agora()
    janela = db.get(RepublicationWindow, (autor_id, post.musica_id))
    if janela is not None and agora < janela.last_at + timedelta(hours=24):
        segundos = math.ceil((janela.last_at + timedelta(hours=24) - agora).total_seconds())
        raise HTTPException(429, "Você pode republicar esta música uma vez a cada 24 horas.",
                            headers={"Retry-After": str(segundos)})
    if janela is None:
        db.add(RepublicationWindow(autor_id=autor_id, musica_id=post.musica_id, last_at=agora))
    else:
        janela.last_at = agora
    aviso = Republication(post_id=post.id, autor_id=autor_id, created_at=agora, comentario=dados.comentario)
    db.add(aviso)
    db.commit()
    db.refresh(aviso)
    return aviso
