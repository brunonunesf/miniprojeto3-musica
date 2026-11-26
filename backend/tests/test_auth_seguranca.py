"""Casos de falha da autenticação, além do contrato do núcleo."""

import pytest
from fastapi import HTTPException
from sqlalchemy import insert, select, text

from app.db import SessionLocal, engine
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import RegistroIn
from app.services.auth import registrar

SENHA = "senha-forte-123"


def registrar_ana(client):
    return client.post("/auth/registro", json={"username": "ana", "name": "  Ana  ", "password": SENHA})


@pytest.mark.parametrize("senha", ["á" * 37, "a" * 73, "🎵" * 19])
def test_senha_acima_de_72_bytes(client, senha):
    registrar_ana(client)
    assert client.post("/auth/registro", json={"username": "bia", "name": "Bia", "password": senha}).status_code == 422
    assert client.post("/auth/login", json={"username": "ana", "password": senha}).status_code == 401


def test_limite_multibyte_e_hash(client):
    senha = "á" * 36
    for username in ("ana", "bia"):
        r = client.post("/auth/registro", json={"username": username, "name": " Ana ", "password": senha})
        assert r.status_code == 201
        assert r.json()["name"] == "Ana"
        assert "password" not in r.json() and "password_hash" not in r.json()
    with SessionLocal() as db:
        users = list(db.scalars(select(User)))
        assert users[0].password_hash != users[1].password_hash
        assert all(user.password_hash != senha for user in users)
    r = client.post("/auth/login", json={"username": "ana", "password": senha})
    assert r.status_code == 200
    eu = client.get("/auth/eu", headers={"Authorization": f"Bearer {r.json()['token']}"})
    assert eu.status_code == 200
    assert "password_hash" not in eu.json()


@pytest.mark.parametrize("hash_", ["", "hash-invalido"])
def test_hash_invalido_nao_retorna_500(client, hash_):
    registrar_ana(client)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "ana"))
        user.password_hash = hash_
        db.commit()
    r = client.post("/auth/login", json={"username": "ana", "password": SENHA})
    inexistente = client.post("/auth/login", json={"username": "ninguem", "password": SENHA})
    assert r.status_code == inexistente.status_code == 401
    assert r.json() == inexistente.json() == {"detail": "usuário ou senha inválidos"}


@pytest.mark.parametrize("authorization", [None, "", "Basic abc", "Bearer ", "Bearer falso", "Bearer abc extra", "bearer abc"])
def test_autorizacao_invalida(client, authorization, monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)
    headers = {"Authorization": authorization} if authorization is not None else {}
    assert client.get("/auth/eu", headers=headers).status_code == 401


@pytest.mark.parametrize("debug", [None, "false", "true"])
def test_bypass_somente_debug(client, monkeypatch, debug):
    user = registrar_ana(client).json()
    if debug is None:
        monkeypatch.delenv("DEBUG", raising=False)
    else:
        monkeypatch.setenv("DEBUG", debug)
    r = client.get("/auth/eu", headers={"X-User-Id": str(user["id"])})
    assert r.status_code == (200 if debug == "true" else 401)
    assert client.get("/auth/eu", headers={"X-User-Id": "99999"}).status_code == 401


def test_sessao_sem_usuario(client, monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)
    # Uma sessão órfã só existe com a chave estrangeira desligada na conexão. Usa UMA conexão explícita
    # do início ao fim: uma `Session` devolve a conexão ao pool no `commit()`, e o `ON` seguinte podia
    # cair em outra, deixando uma conexão com a chave desligada no pool (contaminava os outros testes).
    with engine.connect() as conexao:
        conexao.execute(text("PRAGMA foreign_keys=OFF"))
        try:
            conexao.execute(insert(Session.__table__).values(token="orfao", user_id=99999))
            conexao.commit()
        finally:
            conexao.execute(text("PRAGMA foreign_keys=ON"))
        assert conexao.execute(text("PRAGMA foreign_keys")).scalar() == 1  # religada na mesma conexão
    assert client.get("/auth/eu", headers={"Authorization": "Bearer orfao"}).status_code == 401


def test_nome_vazio(client):
    assert client.post("/auth/registro", json={"username": "ana", "name": "   ", "password": SENHA}).status_code == 422


def test_colisao_na_gravacao(client, monkeypatch):
    registrar_ana(client)
    # Simula uma inserção concorrente entre a consulta inicial e o commit.
    with SessionLocal() as db:
        scalar_original = db.scalar
        chamadas = 0

        def consultar(*args, **kwargs):
            nonlocal chamadas
            chamadas += 1
            return None if chamadas == 1 else scalar_original(*args, **kwargs)

        monkeypatch.setattr(db, "scalar", consultar)
        with pytest.raises(HTTPException) as exc:
            registrar(db, RegistroIn(username="ana", name="Outra", password=SENHA))
        assert exc.value.status_code == 409
        assert db.scalar(select(User).where(User.username == "ana")).name == "Ana"
