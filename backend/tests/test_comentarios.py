from sqlalchemy import func, select

from app.db import SessionLocal
from app.models.comentario import Comentario


def nova_review(client, quem, id_da_musica, chave="demo-horizonte-original"):
    r = client.post("/posts", json={"musica_id": id_da_musica(quem, chave), "nota": 8}, headers=quem)
    assert r.status_code == 201
    return r.json()["id"]


def test_comentar_devolve_o_comentario_com_a_autoria_da_sessao(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia", "Bia")
    post_id = nova_review(client, ana, id_da_musica)

    r = client.post(f"/posts/{post_id}/comentarios", json={"texto": "adorei", "autor_id": 999}, headers=bia)

    assert r.status_code == 201
    assert r.json()["texto"] == "adorei"
    assert r.json()["post_id"] == post_id
    assert r.json()["autor"]["username"] == "bia"  # o autor_id enviado é ignorado


def test_lista_do_mais_antigo_ao_mais_novo(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, ana, id_da_musica)
    for texto in ["um", "dois", "três"]:
        client.post(f"/posts/{post_id}/comentarios", json={"texto": texto}, headers=bia)

    r = client.get(f"/posts/{post_id}/comentarios", headers=ana).json()

    assert [c["texto"] for c in r["items"]] == ["um", "dois", "três"]
    assert (r["total"], r["offset"], r["limit"]) == (3, 0, 50)


def test_empate_de_data_desempata_pelo_id(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)
    for texto in ["um", "dois", "três"]:
        client.post(f"/posts/{post_id}/comentarios", json={"texto": texto}, headers=ana)

    with SessionLocal() as db:  # os três no mesmo instante
        todos = db.query(Comentario).all()
        for comentario in todos:
            comentario.created_at = todos[0].created_at
        db.commit()

    textos = [c["texto"] for c in client.get(f"/posts/{post_id}/comentarios", headers=ana).json()["items"]]

    assert textos == ["um", "dois", "três"]


def test_paginacao_e_fim_da_lista(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)
    for texto in ["um", "dois", "três"]:
        client.post(f"/posts/{post_id}/comentarios", json={"texto": texto}, headers=ana)

    primeira = client.get(f"/posts/{post_id}/comentarios?offset=0&limit=2", headers=ana).json()
    segunda = client.get(f"/posts/{post_id}/comentarios?offset=2&limit=2", headers=ana).json()
    alem = client.get(f"/posts/{post_id}/comentarios?offset=10", headers=ana).json()

    assert [c["texto"] for c in primeira["items"]] == ["um", "dois"]
    assert [c["texto"] for c in segunda["items"]] == ["três"]
    assert primeira["total"] == segunda["total"] == alem["total"] == 3
    assert alem["items"] == []


def test_review_sem_comentarios_devolve_lista_vazia(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)

    assert client.get(f"/posts/{post_id}/comentarios", headers=ana).json()["items"] == []


def test_comentarios_ficam_separados_por_review(client, logar, id_da_musica):
    ana = logar("ana")
    a = nova_review(client, ana, id_da_musica, "demo-horizonte-original")
    b = nova_review(client, ana, id_da_musica, "demo-mare-original")
    client.post(f"/posts/{a}/comentarios", json={"texto": "na A"}, headers=ana)

    assert [c["texto"] for c in client.get(f"/posts/{a}/comentarios", headers=ana).json()["items"]] == ["na A"]
    assert client.get(f"/posts/{b}/comentarios", headers=ana).json()["total"] == 0


def test_texto_invalido_devolve_422_e_nao_grava(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)

    for texto in ["", "   ", "x" * 1001]:
        assert client.post(f"/posts/{post_id}/comentarios", json={"texto": texto}, headers=ana).status_code == 422
    assert client.post(f"/posts/{post_id}/comentarios", json={}, headers=ana).status_code == 422

    assert client.get(f"/posts/{post_id}/comentarios", headers=ana).json()["total"] == 0
    # o limite em si é aceito, e o texto é gravado sem espaços nas pontas
    assert client.post(f"/posts/{post_id}/comentarios", json={"texto": "x" * 1000}, headers=ana).status_code == 201
    r = client.post(f"/posts/{post_id}/comentarios", json={"texto": "  oi  "}, headers=ana)
    assert r.json()["texto"] == "oi"


def test_review_inexistente_devolve_404(client, logar):
    ana = logar("ana")

    assert client.post("/posts/999/comentarios", json={"texto": "oi"}, headers=ana).status_code == 404
    assert client.get("/posts/999/comentarios", headers=ana).status_code == 404


def test_parametros_invalidos_devolvem_422(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)
    enorme = 10**30  # maior que o inteiro do banco: 422, e não 500

    assert client.post(f"/posts/{enorme}/comentarios", json={"texto": "oi"}, headers=ana).status_code == 422
    assert client.get(f"/posts/{enorme}/comentarios", headers=ana).status_code == 422
    for query in ["offset=-1", "limit=0", "limit=101", f"offset={enorme}"]:
        assert client.get(f"/posts/{post_id}/comentarios?{query}", headers=ana).status_code == 422


def test_comentar_e_listar_exigem_login(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)

    assert client.post(f"/posts/{post_id}/comentarios", json={"texto": "oi"}).status_code == 401
    assert client.get(f"/posts/{post_id}/comentarios").status_code == 401


def test_a_review_traz_a_contagem_de_comentarios(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    comentada = nova_review(client, bia, id_da_musica, "demo-mare-original")
    sem_comentario = nova_review(client, bia, id_da_musica, "demo-horizonte-remix")
    client.post("/usuarios/bia/follow", headers=ana)
    client.post(f"/posts/{comentada}/comentarios", json={"texto": "a"}, headers=ana)
    client.post(f"/posts/{comentada}/comentarios", json={"texto": "b"}, headers=bia)

    assert client.get(f"/posts/{comentada}", headers=ana).json()["comentarios"] == 2
    itens = {p["id"]: p["comentarios"] for p in client.get("/feed", headers=ana).json()["items"]}
    assert itens == {comentada: 2, sem_comentario: 0}


def test_comentar_nao_cria_review_nem_altera_a_nota(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    client.post("/usuarios/bia/follow", headers=ana)

    client.post(f"/posts/{post_id}/comentarios", json={"texto": "oi"}, headers=ana)

    feed = client.get("/feed", headers=ana).json()
    assert feed["total"] == 1
    assert feed["items"][0]["nota"] == 8


def test_apagar_a_review_apaga_os_comentarios(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = nova_review(client, bia, id_da_musica)
    client.post(f"/posts/{post_id}/comentarios", json={"texto": "oi"}, headers=ana)

    client.delete(f"/posts/{post_id}", headers=bia)

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Comentario)) == 0
    # uma review nova que reaproveite o id não herda comentários antigos
    novo = nova_review(client, bia, id_da_musica)
    assert client.get(f"/posts/{novo}/comentarios", headers=ana).json()["total"] == 0
