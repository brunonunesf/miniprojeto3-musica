def test_autoria_vem_da_sessao(client, logar, id_da_musica):
    ana = logar("ana", "Ana")

    r = client.post(
        "/posts", json={"musica_id": id_da_musica(ana), "nota": 9, "autor_id": 999}, headers=ana
    )

    assert r.status_code == 201
    assert r.json()["autor"]["username"] == "ana"


def test_review_so_com_a_nota(client, logar, id_da_musica):
    ana = logar("ana")

    r = client.post("/posts", json={"musica_id": id_da_musica(ana), "nota": 7}, headers=ana)

    assert r.status_code == 201
    assert r.json()["nota"] == 7
    assert r.json()["texto"] == ""
    assert r.json()["tem_texto"] is False
    assert r.json()["musica"]["titulo"] == "Horizonte"
    assert r.json()["musica"]["tipo_versao"] == "original"


def test_review_com_texto_tem_indicador(client, logar, id_da_musica):
    ana = logar("ana")

    r = client.post(
        "/posts", json={"musica_id": id_da_musica(ana), "nota": 8, "texto": "linda"}, headers=ana
    )

    assert r.json()["tem_texto"] is True


def test_nota_e_musica_sao_obrigatorias(client, logar, id_da_musica):
    ana = logar("ana")
    musica_id = id_da_musica(ana)

    assert client.post("/posts", json={"nota": 8}, headers=ana).status_code == 422
    assert client.post("/posts", json={"musica_id": musica_id}, headers=ana).status_code == 422
    assert client.post("/posts", json={"texto": "só texto"}, headers=ana).status_code == 422


def test_musica_fora_do_catalogo_devolve_422(client, logar):
    ana = logar("ana")

    for musica_id in [999, 0, -1]:
        r = client.post("/posts", json={"musica_id": musica_id, "nota": 5}, headers=ana)
        assert r.status_code == 422


def test_nota_fora_de_0_a_10_devolve_422(client, logar, id_da_musica):
    ana = logar("ana")
    musica_id = id_da_musica(ana)
    post_id = client.post("/posts", json={"musica_id": musica_id, "nota": 9}, headers=ana).json()["id"]
    outra = id_da_musica(ana, "demo-mare-original")

    for nota in [-1, 11, 7.5, "boa"]:
        assert client.post("/posts", json={"musica_id": outra, "nota": nota}, headers=ana).status_code == 422
        assert client.patch(f"/posts/{post_id}", json={"nota": nota}, headers=ana).status_code == 422

    for nota in [0, 10]:
        assert client.patch(f"/posts/{post_id}", json={"nota": nota}, headers=ana).status_code == 200


def test_pessoas_diferentes_avaliam_a_mesma_musica(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    musica_id = id_da_musica(ana)

    a = client.post("/posts", json={"musica_id": musica_id, "nota": 9}, headers=ana).json()
    b = client.post("/posts", json={"musica_id": musica_id, "nota": 6}, headers=bia).json()

    assert a["musica"]["id"] == b["musica"]["id"] == musica_id


def test_versoes_diferentes_sao_reviews_separadas(client, logar, id_da_musica):
    ana = logar("ana")

    for chave in ["demo-horizonte-original", "demo-horizonte-remix", "demo-horizonte-outro-artista"]:
        r = client.post("/posts", json={"musica_id": id_da_musica(ana, chave), "nota": 8}, headers=ana)
        assert r.status_code == 201


def test_uma_review_por_pessoa_e_versao(client, logar, id_da_musica):
    ana = logar("ana")
    musica_id = id_da_musica(ana)
    post_id = client.post("/posts", json={"musica_id": musica_id, "nota": 9}, headers=ana).json()["id"]

    assert client.post("/posts", json={"musica_id": musica_id, "nota": 3}, headers=ana).status_code == 409

    # apagar libera uma nova review da mesma versão
    client.delete(f"/posts/{post_id}", headers=ana)
    assert client.post("/posts", json={"musica_id": musica_id, "nota": 3}, headers=ana).status_code == 201


def test_editar_ou_apagar_post_alheio_nao_altera_o_banco(client, logar, id_da_musica):
    ana = logar("ana")
    bia = logar("bia")
    post_id = client.post(
        "/posts", json={"musica_id": id_da_musica(ana), "nota": 9, "texto": "da ana"}, headers=ana
    ).json()["id"]

    assert client.patch(f"/posts/{post_id}", json={"texto": "invadido", "nota": 1}, headers=bia).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=bia).status_code == 403

    post = client.get(f"/posts/{post_id}", headers=ana).json()
    assert post["texto"] == "da ana"
    assert post["nota"] == 9


def test_texto_invalido_devolve_422(client, logar, id_da_musica):
    ana = logar("ana")
    musica_id = id_da_musica(ana)
    post_id = client.post(
        "/posts", json={"musica_id": musica_id, "nota": 9, "texto": "ok"}, headers=ana
    ).json()["id"]
    outra = id_da_musica(ana, "demo-mare-original")

    assert client.post("/posts", json={"musica_id": outra, "nota": 5, "texto": "x" * 5001}, headers=ana).status_code == 422
    assert client.patch(f"/posts/{post_id}", json={"texto": "x" * 5001}, headers=ana).status_code == 422
    assert client.patch(f"/posts/{post_id}", json={}, headers=ana).status_code == 422

    assert client.get(f"/posts/{post_id}", headers=ana).json()["texto"] == "ok"

    # o limite em si é aceito
    assert client.patch(f"/posts/{post_id}", json={"texto": "x" * 5000}, headers=ana).status_code == 200


def test_editar_so_a_nota_preserva_o_texto(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = client.post(
        "/posts", json={"musica_id": id_da_musica(ana), "nota": 9, "texto": "gosto muito"}, headers=ana
    ).json()["id"]

    r = client.patch(f"/posts/{post_id}", json={"nota": 5}, headers=ana)

    assert r.json()["nota"] == 5
    assert r.json()["texto"] == "gosto muito"


def test_a_musica_nao_muda_na_edicao(client, logar, id_da_musica):
    ana = logar("ana")
    musica_id = id_da_musica(ana)
    post_id = client.post("/posts", json={"musica_id": musica_id, "nota": 9}, headers=ana).json()["id"]

    r = client.patch(
        f"/posts/{post_id}", json={"nota": 8, "musica_id": id_da_musica(ana, "demo-mare-original")}, headers=ana
    )

    assert r.status_code == 200
    assert r.json()["musica"]["id"] == musica_id


def test_ids_gigantes_devolvem_422_e_nao_500(client, logar, id_da_musica):
    ana = logar("ana")
    enorme = 10**30  # maior que o inteiro do banco
    post_id = client.post("/posts", json={"musica_id": id_da_musica(ana), "nota": 9}, headers=ana).json()["id"]

    assert client.post("/posts", json={"musica_id": enorme, "nota": 5}, headers=ana).status_code == 422
    assert client.get(f"/posts/{enorme}", headers=ana).status_code == 422
    assert client.patch(f"/posts/{enorme}", json={"nota": 5}, headers=ana).status_code == 422
    assert client.delete(f"/posts/{enorme}", headers=ana).status_code == 422
    assert client.get(f"/posts/{post_id}", headers=ana).status_code == 200


def test_envios_simultaneos_da_mesma_review_criam_so_uma(client, logar, id_da_musica):
    from concurrent.futures import ThreadPoolExecutor

    ana = logar("ana")
    corpo = {"musica_id": id_da_musica(ana), "nota": 9}

    with ThreadPoolExecutor(max_workers=6) as pool:
        respostas = list(pool.map(lambda _: client.post("/posts", json=corpo, headers=ana), range(6)))

    assert sorted(r.status_code for r in respostas) == [201, 409, 409, 409, 409, 409]


def test_post_inexistente_devolve_404(client, logar):
    ana = logar("ana")

    assert client.get("/posts/999", headers=ana).status_code == 404
    assert client.patch("/posts/999", json={"texto": "x"}, headers=ana).status_code == 404
    assert client.delete("/posts/999", headers=ana).status_code == 404


def test_posts_exigem_login(client, logar, id_da_musica):
    ana = logar("ana")
    musica_id = id_da_musica(ana)
    post_id = client.post("/posts", json={"musica_id": musica_id, "nota": 9}, headers=ana).json()["id"]

    assert client.post("/posts", json={"musica_id": musica_id, "nota": 9}).status_code == 401
    assert client.get(f"/posts/{post_id}").status_code == 401
    assert client.patch(f"/posts/{post_id}", json={"texto": "y"}).status_code == 401
    assert client.delete(f"/posts/{post_id}").status_code == 401


def test_texto_e_gravado_sem_espacos_nas_pontas(client, logar, id_da_musica):
    ana = logar("ana")

    r = client.post(
        "/posts", json={"musica_id": id_da_musica(ana), "nota": 9, "texto": "  oi  "}, headers=ana
    )

    assert r.json()["texto"] == "oi"
