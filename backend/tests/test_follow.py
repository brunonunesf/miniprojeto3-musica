def test_seguir_e_deixar_de_seguir_atualiza_contadores_e_estado(client, logar):
    ana = logar("ana")
    bia = logar("bia")

    assert client.get("/usuarios/bia", headers=ana).json()["eu_sigo"] is False

    assert client.post("/usuarios/bia/follow", headers=ana).status_code == 204

    bia_vista_por_ana = client.get("/usuarios/bia", headers=ana).json()
    assert (bia_vista_por_ana["seguidores"], bia_vista_por_ana["seguindo"]) == (1, 0)
    assert bia_vista_por_ana["eu_sigo"] is True
    # o estado do botão é de quem olha: a própria bia não segue a bia
    assert client.get("/usuarios/bia", headers=bia).json()["eu_sigo"] is False
    assert client.get("/usuarios/ana", headers=ana).json()["seguindo"] == 1

    assert client.delete("/usuarios/bia/follow", headers=ana).status_code == 204
    depois = client.get("/usuarios/bia", headers=ana).json()
    assert (depois["seguidores"], depois["eu_sigo"]) == (0, False)


def test_seguir_e_deixar_de_seguir_sao_idempotentes(client, logar):
    ana = logar("ana")
    logar("bia")

    for _ in range(3):
        assert client.post("/usuarios/bia/follow", headers=ana).status_code == 204
    assert client.get("/usuarios/bia", headers=ana).json()["seguidores"] == 1

    for _ in range(3):
        assert client.delete("/usuarios/bia/follow", headers=ana).status_code == 204
    # nunca fica negativo
    assert client.get("/usuarios/bia", headers=ana).json()["seguidores"] == 0


def test_seguidores_de_varias_pessoas_sao_contados_separadamente(client, logar):
    ana = logar("ana")
    bia = logar("bia")
    caio = logar("caio")

    client.post("/usuarios/caio/follow", headers=ana)
    client.post("/usuarios/caio/follow", headers=bia)
    client.post("/usuarios/bia/follow", headers=ana)

    caio_visto = client.get("/usuarios/caio", headers=ana).json()
    assert (caio_visto["seguidores"], caio_visto["seguindo"]) == (2, 0)
    ana_vista = client.get("/usuarios/ana", headers=caio).json()
    assert (ana_vista["seguidores"], ana_vista["seguindo"]) == (0, 2)


def test_nao_pode_seguir_a_si_mesmo(client, logar):
    ana = logar("ana")

    assert client.post("/usuarios/ana/follow", headers=ana).status_code == 422
    assert client.get("/usuarios/ana", headers=ana).json()["seguindo"] == 0


def test_seguir_usuario_inexistente_devolve_404(client, logar):
    ana = logar("ana")

    assert client.post("/usuarios/ninguem/follow", headers=ana).status_code == 404
    assert client.delete("/usuarios/ninguem/follow", headers=ana).status_code == 404


def test_follow_exige_login(client, logar):
    logar("bia")

    assert client.post("/usuarios/bia/follow").status_code == 401
    assert client.delete("/usuarios/bia/follow").status_code == 401


def test_seguir_nao_cria_relacao_inversa(client, logar):
    ana = logar("ana")
    bia = logar("bia")

    client.post("/usuarios/bia/follow", headers=ana)

    assert client.get("/usuarios/ana", headers=bia).json()["eu_sigo"] is False
    assert client.get("/usuarios/ana", headers=bia).json()["seguidores"] == 0
