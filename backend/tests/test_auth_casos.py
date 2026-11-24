import pytest

SENHA = "senha-forte-123"


@pytest.mark.parametrize(
    "cabecalho",
    ["Basic abc", "Bearer", "Bearer ", "Bearer token-que-nao-existe"],
)
def test_eu_recusa_cabecalho_invalido(client, cabecalho):
    r = client.get("/auth/eu", headers={"Authorization": cabecalho})

    assert r.status_code == 401


def test_eu_sem_cabecalho_devolve_401(client):
    assert client.get("/auth/eu").status_code == 401


def test_login_de_usuario_sem_senha_devolve_401(client):
    client.post("/usuarios", json={"username": "semsenha", "name": "Sem Senha"})

    r = client.post("/auth/login", json={"username": "semsenha", "password": SENHA})

    assert r.status_code == 401


def test_login_nao_revela_se_o_usuario_existe(client):
    client.post("/auth/registro", json={"username": "ana", "name": "Ana", "password": SENHA})

    senha_errada = client.post("/auth/login", json={"username": "ana", "password": "errada-123"})
    inexistente = client.post("/auth/login", json={"username": "ninguem", "password": SENHA})

    assert senha_errada.status_code == inexistente.status_code == 401
    assert senha_errada.json() == inexistente.json()


def test_nenhuma_resposta_expoe_senha_ou_hash(client, logar):
    registro = client.post(
        "/auth/registro", json={"username": "bia", "name": "Bia", "password": SENHA}
    )
    ana = logar("ana", "Ana")

    respostas = [registro.json(), client.get("/auth/eu", headers=ana).json(), client.get("/usuarios/ana", headers=ana).json()]

    for corpo in respostas:
        assert not any("senha" in chave or "password" in chave or "hash" in chave for chave in corpo)


@pytest.mark.parametrize("senha", ["1234567", "x" * 73])
def test_registro_recusa_senha_fora_dos_limites(client, senha):
    r = client.post("/auth/registro", json={"username": "ana", "name": "Ana", "password": senha})

    assert r.status_code == 422


def test_bypass_so_funciona_com_debug_ligado(client, logar, monkeypatch):
    logar("ana", "Ana")
    usuario_id = client.get("/usuarios").json()["items"][0]["id"]
    cabecalho = {"X-User-Id": str(usuario_id)}

    monkeypatch.delenv("DEBUG", raising=False)
    assert client.get("/auth/eu", headers=cabecalho).status_code == 401

    monkeypatch.setenv("DEBUG", "true")
    assert client.get("/auth/eu", headers=cabecalho).status_code == 200


def test_bypass_com_usuario_inexistente_devolve_401(client, monkeypatch):
    monkeypatch.setenv("DEBUG", "true")

    assert client.get("/auth/eu", headers={"X-User-Id": "99999"}).status_code == 401
