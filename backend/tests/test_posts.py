def review(titulo="Águas de Março", artista="Elis Regina", nota=9, **extra):
    return {"musica": {"titulo": titulo, "artista": artista}, "nota": nota, **extra}


def test_autoria_vem_da_sessao(client, logar):
    ana = logar("ana", "Ana")

    r = client.post("/posts", json={**review(), "autor_id": 999}, headers=ana)

    assert r.status_code == 201
    assert r.json()["autor"]["username"] == "ana"


def test_review_so_com_a_nota(client, logar):
    ana = logar("ana")

    r = client.post("/posts", json=review(nota=7), headers=ana)

    assert r.status_code == 201
    assert r.json()["nota"] == 7
    assert r.json()["texto"] == ""
    assert r.json()["musica"]["titulo"] == "Águas de Março"
    assert r.json()["musica"]["versao"] == "original"


def test_nota_e_musica_sao_obrigatorias(client, logar):
    ana = logar("ana")

    assert client.post("/posts", json={"nota": 8}, headers=ana).status_code == 422
    assert client.post("/posts", json={"musica": review()["musica"]}, headers=ana).status_code == 422
    assert client.post("/posts", json={"texto": "só texto"}, headers=ana).status_code == 422


def test_nota_fora_de_0_a_10_devolve_422(client, logar):
    ana = logar("ana")
    post_id = client.post("/posts", json=review(), headers=ana).json()["id"]

    for nota in [-1, 11, 7.5, "boa"]:
        assert client.post("/posts", json=review("Outra", nota=nota), headers=ana).status_code == 422
        assert client.patch(f"/posts/{post_id}", json={"nota": nota}, headers=ana).status_code == 422

    for nota in [0, 10]:
        assert client.patch(f"/posts/{post_id}", json={"nota": nota}, headers=ana).status_code == 200


def test_mesma_gravacao_compartilha_a_musica(client, logar):
    ana = logar("ana")
    bia = logar("bia")

    a = client.post("/posts", json=review("Águas de Março", "Elis Regina"), headers=ana).json()
    b = client.post("/posts", json=review("  aguas de marco ", "ELIS REGINA", nota=6), headers=bia).json()

    assert a["musica"]["id"] == b["musica"]["id"]


def test_versoes_e_artistas_diferentes_sao_musicas_diferentes(client, logar):
    ana = logar("ana")

    original = client.post("/posts", json=review("Águas de Março", "Elis Regina"), headers=ana).json()
    ao_vivo = client.post(
        "/posts",
        json={"musica": {"titulo": "Águas de Março", "artista": "Elis Regina", "versao": "ao vivo"}, "nota": 8},
        headers=ana,
    ).json()
    outro_artista = client.post("/posts", json=review("Águas de Março", "Tom Jobim"), headers=ana).json()

    ids = {original["musica"]["id"], ao_vivo["musica"]["id"], outro_artista["musica"]["id"]}
    assert len(ids) == 3


def test_uma_review_por_pessoa_e_musica(client, logar):
    ana = logar("ana")
    post_id = client.post("/posts", json=review(), headers=ana).json()["id"]

    assert client.post("/posts", json=review(nota=3), headers=ana).status_code == 409

    # apagar libera uma nova review da mesma música
    client.delete(f"/posts/{post_id}", headers=ana)
    assert client.post("/posts", json=review(nota=3), headers=ana).status_code == 201


def test_editar_ou_apagar_post_alheio_nao_altera_o_banco(client, logar):
    ana = logar("ana")
    bia = logar("bia")
    post_id = client.post("/posts", json=review(texto="da ana"), headers=ana).json()["id"]

    assert client.patch(f"/posts/{post_id}", json={"texto": "invadido", "nota": 1}, headers=bia).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=bia).status_code == 403

    post = client.get(f"/posts/{post_id}", headers=ana).json()
    assert post["texto"] == "da ana"
    assert post["nota"] == 9


def test_texto_invalido_devolve_422(client, logar):
    ana = logar("ana")
    post_id = client.post("/posts", json=review(texto="ok"), headers=ana).json()["id"]

    assert client.post("/posts", json=review("Outra", texto="x" * 5001), headers=ana).status_code == 422
    assert client.patch(f"/posts/{post_id}", json={"texto": "x" * 5001}, headers=ana).status_code == 422
    assert client.patch(f"/posts/{post_id}", json={}, headers=ana).status_code == 422

    assert client.get(f"/posts/{post_id}", headers=ana).json()["texto"] == "ok"

    # o limite em si é aceito
    assert client.patch(f"/posts/{post_id}", json={"texto": "x" * 5000}, headers=ana).status_code == 200


def test_editar_so_a_nota_preserva_o_texto(client, logar):
    ana = logar("ana")
    post_id = client.post("/posts", json=review(texto="gosto muito"), headers=ana).json()["id"]

    r = client.patch(f"/posts/{post_id}", json={"nota": 5}, headers=ana)

    assert r.json()["nota"] == 5
    assert r.json()["texto"] == "gosto muito"


def test_titulo_ou_artista_vazios_devolvem_422(client, logar):
    ana = logar("ana")

    assert client.post("/posts", json=review(titulo="   "), headers=ana).status_code == 422
    assert client.post("/posts", json=review(artista=""), headers=ana).status_code == 422


def test_post_inexistente_devolve_404(client, logar):
    ana = logar("ana")

    assert client.get("/posts/999", headers=ana).status_code == 404
    assert client.patch("/posts/999", json={"texto": "x"}, headers=ana).status_code == 404
    assert client.delete("/posts/999", headers=ana).status_code == 404


def test_posts_exigem_login(client, logar):
    ana = logar("ana")
    post_id = client.post("/posts", json=review(), headers=ana).json()["id"]

    assert client.post("/posts", json=review("Outra")).status_code == 401
    assert client.get(f"/posts/{post_id}").status_code == 401
    assert client.patch(f"/posts/{post_id}", json={"texto": "y"}).status_code == 401
    assert client.delete(f"/posts/{post_id}").status_code == 401


def test_texto_e_gravado_sem_espacos_nas_pontas(client, logar):
    ana = logar("ana")

    r = client.post("/posts", json=review(texto="  oi  "), headers=ana)

    assert r.json()["texto"] == "oi"


def test_capa_e_indicador_de_texto(client, logar):
    ana = logar("ana")
    capa = "https://exemplo.com/capa.jpg"
    musica = {"titulo": "Águas de Março", "artista": "Elis Regina", "capa_url": capa}

    so_nota = client.post("/posts", json={"musica": musica, "nota": 8}, headers=ana).json()
    com_texto = client.post(
        "/posts",
        json={"musica": {**musica, "titulo": "Romaria"}, "nota": 9, "texto": "linda"},
        headers=ana,
    ).json()

    assert so_nota["musica"]["capa_url"] == capa
    assert so_nota["tem_texto"] is False
    assert com_texto["tem_texto"] is True


def test_musica_sem_capa_e_completada_por_outra_review(client, logar):
    ana = logar("ana")
    bia = logar("bia")
    capa = "https://exemplo.com/capa.jpg"

    sem_capa = client.post("/posts", json=review(), headers=ana).json()
    com_capa = client.post(
        "/posts",
        json={"musica": {**review()["musica"], "capa_url": capa}, "nota": 7},
        headers=bia,
    ).json()

    assert sem_capa["musica"]["capa_url"] == ""
    assert com_capa["musica"]["capa_url"] == capa
    assert client.get(f"/posts/{sem_capa['id']}", headers=ana).json()["musica"]["capa_url"] == capa


def test_capa_so_aceita_endereco_http(client, logar):
    ana = logar("ana")

    for capa in ["javascript:alert(1)", "ftp://x.com/a.png", "sem espaço http://x"]:
        musica = {**review()["musica"], "capa_url": capa}
        assert client.post("/posts", json={"musica": musica, "nota": 5}, headers=ana).status_code == 422
