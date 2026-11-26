"""Corrida entre apagar uma review e curtir ou comentar nela (revisão do PR #74).

A consulta que confere se a review existe e a gravação da interação são dois passos. Se outra
sessão apaga a review no meio, a interação não pode ser gravada, nem grudar numa review nova.
"""

import pytest
from sqlalchemy import delete, func, select

from app.db import SessionLocal
from app.models.comentario import Comentario
from app.models.curtida import Curtida
from app.models.post import Post
from app.services import posts as posts_service


def nova_review(client, quem, id_da_musica, chave="demo-horizonte-original"):
    r = client.post("/posts", json={"musica_id": id_da_musica(quem, chave), "nota": 8}, headers=quem)
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture()
def apagar_no_meio_do_caminho(monkeypatch):
    """Faz outra sessão apagar a review (e, se pedido, recriá-la) logo depois de a consulta confirmá-la."""

    def preparar(recriar: bool):
        original = posts_service.buscar
        feito = {"sim": False}

        def buscar_e_apagar(db, post_id):
            post = original(db, post_id)  # a review existe neste instante...
            if not feito["sim"]:
                feito["sim"] = True
                with SessionLocal() as outra:  # ...e outra sessão a apaga antes da gravação
                    autor_id, musica_id = post.autor_id, post.musica_id
                    outra.execute(delete(Post).where(Post.id == post_id))
                    if recriar:
                        outra.add(Post(texto="", nota=5, autor_id=autor_id, musica_id=musica_id))
                    outra.commit()
            return post

        monkeypatch.setattr(posts_service, "buscar", buscar_e_apagar)

    return preparar


@pytest.mark.parametrize("recriar", [False, True])
def test_curtir_review_apagada_no_meio_do_caminho(client, logar, id_da_musica, apagar_no_meio_do_caminho, recriar):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    apagar_no_meio_do_caminho(recriar)

    r = client.post(f"/posts/{post_id}/curtir", headers=ana)

    assert r.status_code == 404
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Curtida)) == 0
        recriada = db.scalar(select(Post.id))
    if recriar:  # a review recriada ganhou outro id e não herdou a curtida
        assert recriada != post_id
        assert client.get(f"/posts/{recriada}", headers=ana).json()["curtidas"] == 0


@pytest.mark.parametrize("recriar", [False, True])
def test_comentar_review_apagada_no_meio_do_caminho(client, logar, id_da_musica, apagar_no_meio_do_caminho, recriar):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    apagar_no_meio_do_caminho(recriar)

    r = client.post(f"/posts/{post_id}/comentarios", json={"texto": "oi"}, headers=ana)

    assert r.status_code == 404
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Comentario)) == 0
        recriada = db.scalar(select(Post.id))
    if recriar:
        assert recriada != post_id
        assert client.get(f"/posts/{recriada}/comentarios", headers=ana).json()["total"] == 0


def test_id_de_review_apagada_nao_e_reaproveitado(client, logar, id_da_musica):
    ana = logar("ana")
    primeiro = nova_review(client, ana, id_da_musica)

    client.delete(f"/posts/{primeiro}", headers=ana)
    segundo = nova_review(client, ana, id_da_musica)

    assert segundo != primeiro
