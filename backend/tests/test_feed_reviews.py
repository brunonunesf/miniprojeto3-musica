from datetime import datetime, timedelta
from app.services import posts
from test_music import popular


def test_feed_edicao_so_review_e_cartao_unico(client, logar, monkeypatch):
    ana, bia, caio = logar('ana'), logar('bia'), logar('caio')
    popular()
    inicio = datetime(2026, 11, 25, 12)
    monkeypatch.setattr(posts, 'agora', lambda: inicio)
    review = client.post('/posts', json={'texto': 'Antiga', 'musica_id': 1}, headers=bia).json()
    texto = client.post('/posts', json={'texto': 'Post texto'}, headers=bia).json()
    monkeypatch.setattr(posts, 'agora', lambda: inicio + timedelta(hours=1))
    recente = client.post('/posts', json={'texto': 'Recente', 'musica_id': 2}, headers=bia).json()
    client.post('/posts', json={'texto': 'Não seguido'}, headers=caio)
    assert client.get('/feed', headers=ana).json()['total'] == 0
    assert client.post('/usuarios/bia/follow', headers=ana).status_code == 204
    def feed(): return client.get('/feed', headers=ana).json()
    assert [p['id'] for p in feed()['items']] == [recente['id'], texto['id'], review['id']]
    monkeypatch.setattr(posts, 'agora', lambda: inicio + timedelta(hours=2))
    client.patch(f"/posts/{texto['id']}", json={'texto': 'Editado sem música'}, headers=bia)
    assert feed()['items'][0]['id'] == recente['id']
    client.patch(f"/posts/{review['id']}", json={'texto': 'Mudei de opinião'}, headers=bia)
    atual = feed()
    assert atual['total'] == 3 and atual['items'][0]['id'] == review['id']
    assert atual['items'][0]['created_at'] == review['created_at']
    data_edicao = atual['items'][0]['feed_at']
    monkeypatch.setattr(posts, 'agora', lambda: inicio + timedelta(hours=3))
    client.patch(f"/posts/{review['id']}", json={'texto': ' Mudei de opinião '}, headers=bia)
    assert feed()['items'][0]['feed_at'] == data_edicao
    client.patch(f"/posts/{review['id']}", json={'texto': 'Outra opinião'}, headers=bia)
    assert feed()['total'] == 3
    assert len({p['feed_id'] for p in feed()['items']}) == 3
    ids = [client.get(f'/feed?offset={i}&limit=1', headers=ana).json()['items'][0]['feed_id'] for i in range(3)]
    assert len(set(ids)) == 3
    assert client.get('/feed?offset=99', headers=ana).json()['items'] == []
    client.delete('/usuarios/bia/follow', headers=ana)
    assert feed()['total'] == 0
    assert client.get('/feed').status_code == 401
    for path in ['/feed?offset=-1', '/feed?limit=101', '/feed?limit=0']:
        assert client.get(path, headers=ana).status_code == 422
    assert client.post('/usuarios/ana/follow', headers=ana).status_code == 422
    assert client.post('/usuarios/ausente/follow', headers=ana).status_code == 404
