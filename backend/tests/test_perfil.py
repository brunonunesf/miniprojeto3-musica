import pytest


def test_editar_e_ver_perfil(client, logar):
    ana = logar("ana", "Ana")

    r = client.patch(
        "/usuarios/eu",
        json={"bio": "oi, sou a ana", "avatar_url": "https://exemplo.com/a.png"},
        headers=ana,
    )
    assert r.status_code == 200
    assert r.json()["bio"] == "oi, sou a ana"

    r = client.get("/usuarios/ana", headers=ana)
    assert r.status_code == 200
    assert r.json()["bio"] == "oi, sou a ana"
    assert r.json()["avatar_url"] == "https://exemplo.com/a.png"
    assert "password_hash" not in r.json()


def test_edicao_parcial_preserva_os_outros_campos(client, logar):
    ana = logar("ana", "Ana")
    client.patch("/usuarios/eu", json={"bio": "minha bio"}, headers=ana)

    r = client.patch("/usuarios/eu", json={"name": "Ana Souza"}, headers=ana)

    assert r.status_code == 200
    assert r.json()["name"] == "Ana Souza"
    assert r.json()["bio"] == "minha bio"


def test_ver_perfil_de_outra_pessoa(client, logar):
    ana = logar("ana", "Ana")
    bia = logar("bia", "Bia")
    client.patch("/usuarios/eu", json={"bio": "sou a bia"}, headers=bia)

    r = client.get("/usuarios/bia", headers=ana)

    assert r.status_code == 200
    assert r.json()["username"] == "bia"
    assert r.json()["bio"] == "sou a bia"


def test_perfil_inexistente_devolve_404(client, logar):
    ana = logar("ana", "Ana")

    r = client.get("/usuarios/ninguem", headers=ana)

    assert r.status_code == 404


def test_perfil_exige_login(client):
    assert client.get("/usuarios/ana").status_code == 401
    assert client.patch("/usuarios/eu", json={"bio": "x"}).status_code == 401


def test_dados_invalidos_devolvem_422(client, logar):
    ana = logar("ana", "Ana")

    assert client.patch("/usuarios/eu", json={"bio": "x" * 281}, headers=ana).status_code == 422
    assert client.patch("/usuarios/eu", json={"avatar_url": "javascript:alert(1)"}, headers=ana).status_code == 422
    assert client.patch("/usuarios/eu", json={"name": ""}, headers=ana).status_code == 422


@pytest.mark.parametrize("username", ["eu", "stats"])
@pytest.mark.parametrize("rota", ["/auth/registro", "/usuarios"])
def test_username_reservado_e_recusado(client, rota, username):
    dados = {"username": username, "name": "Alguém", "password": "senha-forte-123"}

    assert client.post(rota, json=dados).status_code == 422
