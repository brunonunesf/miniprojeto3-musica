"""Apagar comentário: só quem o escreveu (decisão: nem o autor da review apaga o dos outros)."""


def nova_review(client, quem, id_da_musica, chave="demo-horizonte-original"):
    r = client.post("/posts", json={"musica_id": id_da_musica(quem, chave), "nota": 8}, headers=quem)
    assert r.status_code == 201
    return r.json()["id"]


def comentario_de(client, quem, post_id, texto="oi"):
    r = client.post(f"/posts/{post_id}/comentarios", json={"texto": texto}, headers=quem)
    assert r.status_code == 201
    return r.json()["id"]


def test_o_autor_apaga_o_proprio_comentario(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    post_id = nova_review(client, ana, id_da_musica)
    c1, c2 = comentario_de(client, bia, post_id, "um"), comentario_de(client, bia, post_id, "dois")

    r = client.delete(f"/posts/{post_id}/comentarios/{c1}", headers=bia)

    assert r.status_code == 204
    restantes = client.get(f"/posts/{post_id}/comentarios", headers=ana).json()
    assert [c["id"] for c in restantes["items"]] == [c2] and restantes["total"] == 1


def test_o_contador_da_review_diminui_depois_de_apagar(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    post_id = nova_review(client, ana, id_da_musica)
    c = comentario_de(client, bia, post_id)
    assert client.get(f"/posts/{post_id}", headers=ana).json()["comentarios"] == 1

    client.delete(f"/posts/{post_id}/comentarios/{c}", headers=bia)

    assert client.get(f"/posts/{post_id}", headers=ana).json()["comentarios"] == 0


def test_outra_pessoa_nao_apaga_o_comentario(client, logar, id_da_musica):
    ana, bia, caio = logar("ana"), logar("bia"), logar("caio")
    post_id = nova_review(client, ana, id_da_musica)
    c = comentario_de(client, bia, post_id)

    for intruso in (caio, ana):  # nem o autor da review
        assert client.delete(f"/posts/{post_id}/comentarios/{c}", headers=intruso).status_code == 403

    assert client.get(f"/posts/{post_id}/comentarios", headers=ana).json()["total"] == 1


def test_apagar_comentario_exige_login(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    post_id = nova_review(client, ana, id_da_musica)
    c = comentario_de(client, bia, post_id)

    assert client.delete(f"/posts/{post_id}/comentarios/{c}").status_code == 401


def test_comentario_inexistente_ou_de_outra_review_da_404(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    p1 = nova_review(client, ana, id_da_musica)
    p2 = nova_review(client, bia, id_da_musica, chave="demo-mare-original")
    c = comentario_de(client, bia, p1)

    assert client.delete(f"/posts/{p1}/comentarios/9999", headers=bia).status_code == 404
    assert client.delete(f"/posts/{p2}/comentarios/{c}", headers=bia).status_code == 404  # é de outra review
    assert client.delete(f"/posts/{p1}/comentarios/{c}", headers=bia).status_code == 204
    assert client.delete(f"/posts/{p1}/comentarios/{c}", headers=bia).status_code == 404  # segunda vez


def test_ids_gigantes_viram_422_e_nao_500(client, logar, id_da_musica):
    ana = logar("ana")
    post_id = nova_review(client, ana, id_da_musica)

    assert client.delete(f"/posts/{post_id}/comentarios/{2**70}", headers=ana).status_code == 422
