def avaliar(client, quem, id_da_musica, chave, texto="", nota=8):
    musica_id = id_da_musica(quem, chave)
    r = client.post("/posts", json={"musica_id": musica_id, "nota": nota, "texto": texto}, headers=quem)
    assert r.status_code == 201
    return r.json()


def test_pessoa_sem_reviews_devolve_lista_vazia(client, logar):
    ana = logar("ana")
    logar("bia")

    r = client.get("/usuarios/bia/posts", headers=ana)

    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "offset": 0, "limit": 10}


def test_traz_so_as_reviews_da_pessoa_da_mais_nova_para_a_mais_antiga(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    avaliar(client, bia, id_da_musica, "demo-horizonte-original", "primeira")
    avaliar(client, bia, id_da_musica, "demo-mare-original", "segunda")
    avaliar(client, ana, id_da_musica, "demo-mare-original", "da ana")

    r = client.get("/usuarios/bia/posts", headers=ana).json()

    assert [p["texto"] for p in r["items"]] == ["segunda", "primeira"]
    assert r["total"] == 2
    assert {p["autor"]["username"] for p in r["items"]} == {"bia"}


def test_qualquer_pessoa_logada_ve_as_reviews_de_outra(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    avaliar(client, bia, id_da_musica, "demo-mare-original", "da bia")

    # sem seguir: o perfil é público para quem está logado, ao contrário do feed
    assert client.get("/usuarios/bia/posts", headers=ana).json()["total"] == 1
    assert client.get("/feed", headers=ana).json()["total"] == 0


def test_paginacao_e_fim_da_lista(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    for i, chave in enumerate(["demo-horizonte-original", "demo-horizonte-remix", "demo-mare-original"]):
        avaliar(client, bia, id_da_musica, chave, texto=f"r{i}")

    primeira = client.get("/usuarios/bia/posts?offset=0&limit=2", headers=ana).json()
    segunda = client.get("/usuarios/bia/posts?offset=2&limit=2", headers=ana).json()
    alem = client.get("/usuarios/bia/posts?offset=10", headers=ana).json()

    assert [p["texto"] for p in primeira["items"]] == ["r2", "r1"]
    assert [p["texto"] for p in segunda["items"]] == ["r0"]
    assert primeira["total"] == segunda["total"] == alem["total"] == 3
    assert alem["items"] == []


def test_itens_trazem_musica_nota_e_interacoes_de_quem_olha(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    review = avaliar(client, bia, id_da_musica, "demo-horizonte-remix", "linda", nota=9)
    client.post(f"/posts/{review['id']}/curtir", headers=ana)
    client.post(f"/posts/{review['id']}/comentarios", json={"texto": "oi"}, headers=ana)

    item = client.get("/usuarios/bia/posts", headers=ana).json()["items"][0]

    assert (item["musica"]["tipo_versao"], item["nota"], item["tem_texto"]) == ("remix", 9, True)
    assert (item["curtidas"], item["curtido_por_mim"], item["comentarios"]) == (1, True, 1)


def test_review_apagada_sai_do_perfil(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    review = avaliar(client, bia, id_da_musica, "demo-mare-original")

    client.delete(f"/posts/{review['id']}", headers=bia)

    assert client.get("/usuarios/bia/posts", headers=ana).json()["total"] == 0


def test_usuario_inexistente_devolve_404(client, logar):
    ana = logar("ana")

    assert client.get("/usuarios/ninguem/posts", headers=ana).status_code == 404


def test_parametros_invalidos_devolvem_422(client, logar):
    ana = logar("ana")
    enorme = 10**30  # maior que o inteiro do banco: 422, e não 500

    for query in ["offset=-1", "limit=0", "limit=101", f"offset={enorme}", "limit=abc"]:
        assert client.get(f"/usuarios/ana/posts?{query}", headers=ana).status_code == 422


def test_exige_login(client, logar):
    logar("bia")

    assert client.get("/usuarios/bia/posts").status_code == 401
