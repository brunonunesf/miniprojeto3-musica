from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from fastapi import HTTPException
from sqlalchemy import select
from app.db import SessionLocal
from app.models.post import Post
from app.models.republication import Republication
from app.schemas.republication import RepublicationCreate
from app.services import posts, republications
from test_music import popular


def test_republicar_limite_edicao_e_exclusao(client, logar, monkeypatch):
    ana, bia = logar('ana'), logar('bia')
    popular()
    inicio = datetime(2026, 11, 25, 12)
    monkeypatch.setattr(posts, 'agora', lambda: inicio)
    p = client.post('/posts', json={'texto': 'Minha review', 'musica_id': 1}, headers=ana).json()
    url = f"/posts/{p['id']}/republicacoes"
    assert client.post(url, json={}).status_code == 401
    assert client.post(url, json={}, headers=bia).status_code == 403
    assert client.post('/posts/999/republicacoes', json={}, headers=ana).status_code == 404
    assert client.post(url, json={'comentario': 'x'*281}, headers=ana).status_code == 422
    texto = client.post('/posts', json={'texto': 'Sem música'}, headers=ana).json()
    assert client.post(f"/posts/{texto['id']}/republicacoes", json={}, headers=ana).status_code == 422
    aviso = client.post(url, json={'comentario': 'Continua boa!'}, headers=ana)
    assert aviso.status_code == 201
    data = aviso.json()['created_at']
    client.post('/usuarios/ana/follow', headers=bia)
    def feed(): return client.get('/feed', headers=bia).json()
    assert feed()['total'] == 3
    assert len({p['feed_id'] for p in feed()['items']}) == 3
    monkeypatch.setattr(posts, 'agora', lambda: inicio + timedelta(hours=1))
    client.patch(f"/posts/{p['id']}", json={'texto': 'Mudei de ideia'}, headers=ana)
    antigo = next(i for i in feed()['items'] if i['tipo'] == 'republicacao')
    assert antigo['texto'] == 'Mudei de ideia'
    assert antigo['comentario'] == 'Continua boa!' and antigo['feed_at'] == data
    monkeypatch.setattr(posts, 'agora', lambda: inicio + timedelta(hours=24) - timedelta(microseconds=1))
    recusada = client.post(url, json={}, headers=ana)
    assert recusada.status_code == 429 and int(recusada.headers['Retry-After']) >= 1
    monkeypatch.setattr(posts, 'agora', lambda: inicio + timedelta(hours=24))
    assert client.post(url, json={}, headers=ana).status_code == 201
    assert feed()['total'] == 4
    assert client.delete(f"/posts/{p['id']}", headers=ana).status_code == 204
    assert feed()['total'] == 1
    assert client.post(url, json={}, headers=ana).status_code == 404
    nova = client.post('/posts', json={'texto': 'Nova raiz', 'musica_id': 1}, headers=ana).json()
    assert nova['id'] != p['id']
    assert client.post(f"/posts/{nova['id']}/republicacoes", json={}, headers=ana).status_code == 429
    with SessionLocal() as db:
        assert list(db.scalars(select(Republication))) == []
        assert len(list(db.scalars(select(Post)))) == 3


def test_republicacoes_concorrentes(client, logar, monkeypatch):
    ana = logar('ana'); popular()
    p = client.post('/posts', json={'texto': 'Review', 'musica_id': 1}, headers=ana).json()
    barreira = Barrier(2)
    def executar(_):
        with SessionLocal() as db:
            barreira.wait(timeout=5)
            try:
                republications.criar(db, p['id'], RepublicationCreate(), p['autor']['id'])
                return 201
            except HTTPException as e:
                return e.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(executar, range(2))) == [201, 429]
    with SessionLocal() as db:
        assert len(list(db.scalars(select(Republication)))) == 1


def test_reinicio_preserva_review_catalogo_e_limite(client, logar):
    from fastapi.testclient import TestClient
    from app.main import app
    ana = logar('ana'); popular()
    review = client.post('/posts', json={'texto': 'Persistente', 'musica_id': 1}, headers=ana).json()
    url = f"/posts/{review['id']}/republicacoes"
    assert client.post(url, json={}, headers=ana).status_code == 201
    with TestClient(app) as reiniciado:
        assert reiniciado.get('/auth/eu', headers=ana).json()['username'] == 'ana'
        assert reiniciado.get(f"/posts/{review['id']}", headers=ana).json()['texto'] == 'Persistente'
        assert reiniciado.get('/musicas', headers=ana).json()['total'] == 6
        assert reiniciado.post(url, json={}, headers=ana).status_code == 429
