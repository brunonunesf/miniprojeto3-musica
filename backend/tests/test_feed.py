from app.db import SessionLocal
from app.models.post import Post


def avaliar(client, quem, id_da_musica, chave, texto="", nota=8):
    musica_id = id_da_musica(quem, chave)
    r = client.post("/posts", json={"musica_id": musica_id, "nota": nota, "texto": texto}, headers=quem)
    assert r.status_code == 201
    return r.json()


def test_feed_de_quem_nao_segue_ninguem_e_vazio(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    avaliar(client, bia, id_da_musica, "demo-mare-original")

    r = client.get("/feed", headers=ana)

    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "offset": 0, "limit": 10}


def test_feed_nao_inclui_as_proprias_reviews(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    avaliar(client, ana, id_da_musica, "demo-mare-original", "minha")
    avaliar(client, bia, id_da_musica, "demo-mare-original", "da bia")
    client.post("/usuarios/bia/follow", headers=ana)

    textos = [p["texto"] for p in client.get("/feed", headers=ana).json()["items"]]

    assert textos == ["da bia"]


def test_feed_traz_o_cartao_da_review(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia", "Bia")
    avaliar(client, bia, id_da_musica, "demo-horizonte-remix", nota=9)
    avaliar(client, bia, id_da_musica, "demo-mare-original", texto="linda", nota=7)
    client.post("/usuarios/bia/follow", headers=ana)

    mare, horizonte = client.get("/feed", headers=ana).json()["items"]

    assert (mare["musica"]["titulo"], mare["nota"], mare["tem_texto"]) == ("Maré", 7, True)
    assert mare["autor"]["username"] == "bia"
    assert (horizonte["musica"]["tipo_versao"], horizonte["nota"], horizonte["tem_texto"]) == ("remix", 9, False)
    assert "capa_url" in mare["musica"]


def test_paginacao_e_fim_da_lista(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    for i, chave in enumerate(["demo-horizonte-original", "demo-horizonte-remix", "demo-mare-original"]):
        avaliar(client, bia, id_da_musica, chave, texto=f"r{i}")
    client.post("/usuarios/bia/follow", headers=ana)

    primeira = client.get("/feed?offset=0&limit=2", headers=ana).json()
    segunda = client.get("/feed?offset=2&limit=2", headers=ana).json()
    alem = client.get("/feed?offset=10&limit=2", headers=ana).json()

    assert [p["texto"] for p in primeira["items"]] == ["r2", "r1"]
    assert [p["texto"] for p in segunda["items"]] == ["r0"]
    assert primeira["total"] == segunda["total"] == alem["total"] == 3  # conta o conjunto inteiro
    assert alem["items"] == []


def test_empate_de_data_desempata_pelo_id(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    for i, chave in enumerate(["demo-horizonte-original", "demo-horizonte-remix", "demo-mare-original"]):
        avaliar(client, bia, id_da_musica, chave, texto=f"r{i}")
    client.post("/usuarios/bia/follow", headers=ana)

    with SessionLocal() as db:  # as três reviews no mesmo instante
        instante = db.query(Post).first().created_at
        for post in db.query(Post):
            post.created_at = instante
        db.commit()

    textos = [p["texto"] for p in client.get("/feed", headers=ana).json()["items"]]

    assert textos == ["r2", "r1", "r0"]


def test_feed_acompanha_follow_e_unfollow(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    avaliar(client, bia, id_da_musica, "demo-mare-original", "da bia")

    assert client.get("/feed", headers=ana).json()["total"] == 0
    client.post("/usuarios/bia/follow", headers=ana)
    assert client.get("/feed", headers=ana).json()["total"] == 1
    client.delete("/usuarios/bia/follow", headers=ana)
    assert client.get("/feed", headers=ana).json()["total"] == 0


def test_review_apagada_sai_do_feed(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post = avaliar(client, bia, id_da_musica, "demo-mare-original")
    client.post("/usuarios/bia/follow", headers=ana)

    client.delete(f"/posts/{post['id']}", headers=bia)

    assert client.get("/feed", headers=ana).json()["total"] == 0


def test_parametros_invalidos_devolvem_422(client, logar):
    ana = logar("ana")
    enorme = 10**30  # maior que o inteiro do banco: 422, e não 500

    for query in ["offset=-1", "limit=0", "limit=101", f"offset={enorme}", "limit=abc"]:
        assert client.get(f"/feed?{query}", headers=ana).status_code == 422


def test_feed_exige_login(client):
    assert client.get("/feed").status_code == 401
