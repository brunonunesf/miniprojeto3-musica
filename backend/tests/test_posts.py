def test_autoria_vem_da_sessao(client, logar):
    ana = logar("ana", "Ana")

    r = client.post("/posts", json={"texto": "oi", "autor_id": 999}, headers=ana)

    assert r.status_code == 201
    assert r.json()["autor"]["username"] == "ana"


def test_editar_ou_apagar_post_alheio_nao_altera_o_banco(client, logar):
    ana = logar("ana")
    bia = logar("bia")
    post_id = client.post("/posts", json={"texto": "da ana"}, headers=ana).json()["id"]

    assert client.patch(f"/posts/{post_id}", json={"texto": "invadido"}, headers=bia).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=bia).status_code == 403

    assert client.get(f"/posts/{post_id}", headers=ana).json()["texto"] == "da ana"


def test_texto_invalido_devolve_422(client, logar):
    ana = logar("ana")
    post_id = client.post("/posts", json={"texto": "ok"}, headers=ana).json()["id"]

    for texto in ["", "   ", "x" * 501]:
        assert client.post("/posts", json={"texto": texto}, headers=ana).status_code == 422
        assert client.patch(f"/posts/{post_id}", json={"texto": texto}, headers=ana).status_code == 422

    assert client.get(f"/posts/{post_id}", headers=ana).json()["texto"] == "ok"


def test_post_inexistente_devolve_404(client, logar):
    ana = logar("ana")

    assert client.get("/posts/999", headers=ana).status_code == 404
    assert client.patch("/posts/999", json={"texto": "x"}, headers=ana).status_code == 404
    assert client.delete("/posts/999", headers=ana).status_code == 404


def test_posts_exigem_login(client, logar):
    ana = logar("ana")
    post_id = client.post("/posts", json={"texto": "x"}, headers=ana).json()["id"]

    assert client.post("/posts", json={"texto": "x"}).status_code == 401
    assert client.get(f"/posts/{post_id}").status_code == 401
    assert client.patch(f"/posts/{post_id}", json={"texto": "y"}).status_code == 401
    assert client.delete(f"/posts/{post_id}").status_code == 401


def test_texto_e_gravado_sem_espacos_nas_pontas(client, logar):
    ana = logar("ana")

    r = client.post("/posts", json={"texto": "  oi  "}, headers=ana)

    assert r.json()["texto"] == "oi"
