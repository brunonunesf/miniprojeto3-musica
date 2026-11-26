from sqlalchemy import func, select

from app.db import SessionLocal
from app.models.curtida import Curtida


def nova_review(client, quem, id_da_musica, chave="demo-horizonte-original"):
    r = client.post("/posts", json={"musica_id": id_da_musica(quem, chave), "nota": 8}, headers=quem)
    assert r.status_code == 201
    return r.json()["id"]


def test_curtir_devolve_contagem_e_estado(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)

    r = client.post(f"/posts/{post_id}/curtir", headers=ana)

    assert r.status_code == 200
    assert r.json() == {"curtidas": 1, "curtido_por_mim": True}


def test_curtir_e_descurtir_sao_idempotentes(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)

    for _ in range(3):
        assert client.post(f"/posts/{post_id}/curtir", headers=ana).json()["curtidas"] == 1
    for _ in range(3):
        assert client.delete(f"/posts/{post_id}/curtir", headers=ana).json() == {
            "curtidas": 0,
            "curtido_por_mim": False,
        }  # nunca fica negativo


def test_a_contagem_soma_pessoas_diferentes(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    caio = logar("caio")
    post_id = nova_review(client, bia, id_da_musica)

    client.post(f"/posts/{post_id}/curtir", headers=ana)
    client.post(f"/posts/{post_id}/curtir", headers=caio)

    assert client.get(f"/posts/{post_id}", headers=bia).json()["curtidas"] == 2
    # descurtir tira só a curtida de quem pediu
    assert client.delete(f"/posts/{post_id}/curtir", headers=ana).json()["curtidas"] == 1


def test_o_estado_e_de_quem_olha(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    client.post(f"/posts/{post_id}/curtir", headers=ana)

    vista_por_ana = client.get(f"/posts/{post_id}", headers=ana).json()
    vista_por_bia = client.get(f"/posts/{post_id}", headers=bia).json()

    assert (vista_por_ana["curtidas"], vista_por_ana["curtido_por_mim"]) == (1, True)
    assert (vista_por_bia["curtidas"], vista_por_bia["curtido_por_mim"]) == (1, False)


def test_curtir_a_propria_review_e_permitido(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)

    r = client.post(f"/posts/{post_id}/curtir", headers=ana)

    assert r.json() == {"curtidas": 1, "curtido_por_mim": True}


def test_curtir_nao_cria_review_nem_altera_a_nota(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    client.post("/usuarios/bia/follow", headers=ana)

    client.post(f"/posts/{post_id}/curtir", headers=ana)

    feed = client.get("/feed", headers=ana).json()
    assert feed["total"] == 1  # nenhuma review nova
    assert feed["items"][0]["nota"] == 8
    assert client.get("/feed", headers=bia).json()["total"] == 0


def test_post_inexistente_devolve_404(client, logar):
    ana = logar("ana")

    assert client.post("/posts/999/curtir", headers=ana).status_code == 404
    assert client.delete("/posts/999/curtir", headers=ana).status_code == 404


def test_id_gigante_devolve_422(client, logar):
    ana = logar("ana")

    assert client.post(f"/posts/{10**30}/curtir", headers=ana).status_code == 422
    assert client.delete(f"/posts/{10**30}/curtir", headers=ana).status_code == 422


def test_curtir_exige_login(client, logar, id_da_musica):
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)

    assert client.post(f"/posts/{post_id}/curtir").status_code == 401
    assert client.delete(f"/posts/{post_id}/curtir").status_code == 401


def test_feed_traz_as_curtidas_de_cada_review(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    caio = logar("caio")
    curtida = nova_review(client, bia, id_da_musica, "demo-mare-original")
    sem_curtida = nova_review(client, bia, id_da_musica, "demo-horizonte-remix")
    client.post("/usuarios/bia/follow", headers=ana)
    client.post(f"/posts/{curtida}/curtir", headers=ana)
    client.post(f"/posts/{curtida}/curtir", headers=caio)

    itens = {p["id"]: p for p in client.get("/feed", headers=ana).json()["items"]}

    assert (itens[curtida]["curtidas"], itens[curtida]["curtido_por_mim"]) == (2, True)
    assert (itens[sem_curtida]["curtidas"], itens[sem_curtida]["curtido_por_mim"]) == (0, False)


def test_editar_a_review_mostra_as_curtidas(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    client.post(f"/posts/{post_id}/curtir", headers=ana)

    r = client.patch(f"/posts/{post_id}", json={"nota": 3}, headers=bia)

    assert (r.json()["curtidas"], r.json()["curtido_por_mim"]) == (1, False)


def test_apagar_a_review_apaga_as_curtidas(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    client.post(f"/posts/{post_id}/curtir", headers=ana)

    client.delete(f"/posts/{post_id}", headers=bia)

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Curtida)) == 0
    assert client.post(f"/posts/{post_id}/curtir", headers=ana).status_code == 404

    # uma review nova que reaproveite o id não herda curtidas antigas
    novo = nova_review(client, bia, id_da_musica)
    assert client.get(f"/posts/{novo}", headers=ana).json()["curtidas"] == 0
