from app.db import SessionLocal
from app.models.post import Post

CHAVES = [
    "demo-horizonte-original",
    "demo-horizonte-remix",
    "demo-horizonte-vivo",
    "demo-horizonte-remaster",
    "demo-horizonte-outro-artista",
    "demo-mare-original",
]


def avaliar(client, quem, id_da_musica, chave, texto="", nota=8):
    r = client.post(
        "/posts", json={"musica_id": id_da_musica(quem, chave), "nota": nota, "texto": texto}, headers=quem
    )
    assert r.status_code == 201
    return r.json()


def ranking(client, quem, query=""):
    r = client.get(f"/musicas/populares{query}", headers=quem)
    assert r.status_code == 200
    return r.json()


def test_sem_reviews_a_vitrine_e_vazia(client, logar):
    ana = logar("ana")

    assert ranking(client, ana) == {"items": [], "total": 0, "offset": 0, "limit": 10}


def test_ordena_por_quantidade_e_so_traz_musicas_com_reviews(client, logar, id_da_musica):
    ana, bia, caio = logar("ana"), logar("bia"), logar("caio")
    for quem in (ana, bia, caio):
        avaliar(client, quem, id_da_musica, "demo-mare-original")
    for quem in (ana, bia):
        avaliar(client, quem, id_da_musica, "demo-horizonte-remix")
    avaliar(client, ana, id_da_musica, "demo-horizonte-original")

    itens = ranking(client, ana)["items"]

    assert [(m["chave_catalogo"], m["quantidade_reviews"]) for m in itens] == [
        ("demo-mare-original", 3),
        ("demo-horizonte-remix", 2),
        ("demo-horizonte-original", 1),
    ]  # as outras 3 músicas do catálogo, sem reviews, ficam de fora
    assert ranking(client, ana)["total"] == 3


def test_empate_desempata_pelo_id_da_musica(client, logar, id_da_musica):
    ana = logar("ana")
    # mesma quantidade (1 cada), avaliadas em ordem inversa à do catálogo
    for chave in ["demo-mare-original", "demo-horizonte-remix", "demo-horizonte-original"]:
        avaliar(client, ana, id_da_musica, chave)

    chaves = [m["chave_catalogo"] for m in ranking(client, ana)["items"]]

    assert chaves == ["demo-horizonte-original", "demo-horizonte-remix", "demo-mare-original"]


def test_versoes_do_mesmo_titulo_sao_contadas_separadas(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    avaliar(client, ana, id_da_musica, "demo-horizonte-original")
    avaliar(client, bia, id_da_musica, "demo-horizonte-original")
    avaliar(client, ana, id_da_musica, "demo-horizonte-remix")
    avaliar(client, ana, id_da_musica, "demo-horizonte-outro-artista")

    contagens = {m["chave_catalogo"]: m["quantidade_reviews"] for m in ranking(client, ana)["items"]}

    assert contagens == {
        "demo-horizonte-original": 2,
        "demo-horizonte-remix": 1,
        "demo-horizonte-outro-artista": 1,
    }


def test_item_traz_os_dados_do_catalogo_e_a_quantidade(client, logar, id_da_musica):
    ana = logar("ana")
    avaliar(client, ana, id_da_musica, "demo-mare-original")

    item = ranking(client, ana)["items"][0]

    assert {"id", "chave_catalogo", "titulo", "artista", "tipo_versao", "generos", "tags", "capa_url"} <= item.keys()
    assert item["quantidade_reviews"] == 1


def test_curtir_comentar_editar_e_seguir_nao_mudam_a_contagem(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    review = avaliar(client, bia, id_da_musica, "demo-mare-original")

    client.post(f"/posts/{review['id']}/curtir", headers=ana)
    client.post(f"/posts/{review['id']}/comentarios", json={"texto": "oi"}, headers=ana)
    client.patch(f"/posts/{review['id']}", json={"nota": 2, "texto": "mudei"}, headers=bia)
    client.post("/usuarios/bia/follow", headers=ana)

    assert ranking(client, ana)["items"][0]["quantidade_reviews"] == 1


def test_apagar_a_review_reduz_e_a_musica_sem_reviews_sai(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    da_ana = avaliar(client, ana, id_da_musica, "demo-mare-original")
    da_bia = avaliar(client, bia, id_da_musica, "demo-mare-original")

    client.delete(f"/posts/{da_ana['id']}", headers=ana)
    assert ranking(client, ana)["items"][0]["quantidade_reviews"] == 1

    client.delete(f"/posts/{da_bia['id']}", headers=bia)
    assert ranking(client, ana)["items"] == []


def test_paginacao_e_fim_da_lista(client, logar, id_da_musica):
    ana = logar("ana")
    for chave in CHAVES[:3]:
        avaliar(client, ana, id_da_musica, chave)

    primeira = ranking(client, ana, "?offset=0&limit=2")
    segunda = ranking(client, ana, "?offset=2&limit=2")
    alem = ranking(client, ana, "?offset=10")

    assert (len(primeira["items"]), len(segunda["items"]), len(alem["items"])) == (2, 1, 0)
    assert primeira["total"] == segunda["total"] == alem["total"] == 3  # conta todas as músicas com review


def test_populares_nao_e_lido_como_id_de_musica(client, logar):
    ana = logar("ana")

    assert client.get("/musicas/populares", headers=ana).status_code == 200


def test_populares_parametros_invalidos_e_login(client, logar):
    ana = logar("ana")
    enorme = 10**30

    for query in ["offset=-1", "limit=0", "limit=101", f"offset={enorme}", "limit=abc"]:
        assert client.get(f"/musicas/populares?{query}", headers=ana).status_code == 422
    assert client.get("/musicas/populares").status_code == 401


# ---------- GET /musicas/{id}/reviews ----------


def test_reviews_da_musica_da_mais_nova_para_a_mais_antiga(client, logar, id_da_musica):
    ana, bia, caio = logar("ana"), logar("bia"), logar("caio")
    avaliar(client, bia, id_da_musica, "demo-mare-original", "primeira")
    avaliar(client, caio, id_da_musica, "demo-mare-original", "segunda")
    avaliar(client, caio, id_da_musica, "demo-horizonte-remix", "outra música")
    musica_id = id_da_musica(ana, "demo-mare-original")

    r = client.get(f"/musicas/{musica_id}/reviews", headers=ana).json()

    assert [p["texto"] for p in r["items"]] == ["segunda", "primeira"]
    assert (r["total"], r["offset"], r["limit"]) == (2, 0, 10)


def test_reviews_da_musica_so_da_gravacao_pedida(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    avaliar(client, bia, id_da_musica, "demo-horizonte-original", "original")
    avaliar(client, bia, id_da_musica, "demo-horizonte-remix", "remix")

    remix = id_da_musica(ana, "demo-horizonte-remix")
    textos = [p["texto"] for p in client.get(f"/musicas/{remix}/reviews", headers=ana).json()["items"]]

    assert textos == ["remix"]


def test_musica_sem_reviews_devolve_lista_vazia_e_inexistente_404(client, logar, id_da_musica):
    ana = logar("ana")

    vazia = client.get(f"/musicas/{id_da_musica(ana)}/reviews", headers=ana)
    assert vazia.status_code == 200 and vazia.json()["items"] == []
    assert client.get("/musicas/99999/reviews", headers=ana).status_code == 404


def test_reviews_da_musica_trazem_as_interacoes_de_quem_olha(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    review = avaliar(client, bia, id_da_musica, "demo-mare-original", "linda", nota=9)
    client.post(f"/posts/{review['id']}/curtir", headers=ana)
    client.post(f"/posts/{review['id']}/comentarios", json={"texto": "oi"}, headers=ana)

    item = client.get(f"/musicas/{id_da_musica(ana, 'demo-mare-original')}/reviews", headers=ana).json()["items"][0]

    assert (item["nota"], item["tem_texto"], item["autor"]["username"]) == (9, True, "bia")
    assert (item["curtidas"], item["curtido_por_mim"], item["comentarios"]) == (1, True, 1)


def test_reviews_da_musica_empate_de_data_desempata_pelo_id(client, logar, id_da_musica):
    ana, bia, caio = logar("ana"), logar("bia"), logar("caio")
    for quem, texto in ((ana, "r0"), (bia, "r1"), (caio, "r2")):
        avaliar(client, quem, id_da_musica, "demo-mare-original", texto)

    with SessionLocal() as db:  # as três no mesmo instante
        todas = db.query(Post).all()
        for post in todas:
            post.created_at = todas[0].created_at
        db.commit()

    musica = id_da_musica(ana, "demo-mare-original")
    textos = [p["texto"] for p in client.get(f"/musicas/{musica}/reviews", headers=ana).json()["items"]]

    assert textos == ["r2", "r1", "r0"]


def test_reviews_da_musica_paginacao_parametros_e_login(client, logar, id_da_musica):
    ana, bia, caio = logar("ana"), logar("bia"), logar("caio")
    for quem in (ana, bia, caio):
        avaliar(client, quem, id_da_musica, "demo-mare-original")
    musica = id_da_musica(ana, "demo-mare-original")
    enorme = 10**30

    pagina = client.get(f"/musicas/{musica}/reviews?offset=2&limit=2", headers=ana).json()
    assert (len(pagina["items"]), pagina["total"]) == (1, 3)
    for query in ["offset=-1", "limit=0", "limit=101", f"offset={enorme}"]:
        assert client.get(f"/musicas/{musica}/reviews?{query}", headers=ana).status_code == 422
    assert client.get(f"/musicas/{enorme}/reviews", headers=ana).status_code == 422
    assert client.get(f"/musicas/{musica}/reviews").status_code == 401
