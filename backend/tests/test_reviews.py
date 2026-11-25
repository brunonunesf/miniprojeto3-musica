from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.db import SessionLocal
from app.models.post import Post
from app.schemas.post import PostCreate
from app.services import posts
from test_music import popular


def criar(client, h, musica=1, texto='Minha opinião'):
    return client.post('/posts', json={'texto': texto, 'musica_id': musica}, headers=h)


def test_reviews_identidade_permissoes_e_exclusao(client, logar):
    ana, bia = logar('ana'), logar('bia')
    popular()
    a = criar(client, ana).json()
    b = criar(client, bia).json()
    assert a['musica']['id'] == b['musica']['id'] == 1
    assert a['autor']['username'] == 'ana'
    duplicate = criar(client, ana)
    assert duplicate.status_code == 409
    assert duplicate.json()['detail']['post_id'] == a['id']
    assert criar(client, ana, musica=2).status_code == 201
    assert criar(client, ana, musica=999).status_code == 422
    url = f"/posts/{a['id']}"
    assert client.patch(url, json={'texto': 'Outro'}, headers=bia).status_code == 403
    assert client.delete(url, headers=bia).status_code == 403
    for patch in [{'texto': '  '}, {'texto': 'x', 'musica_id': 2}, {'texto': 'x', 'musica_id': None}]:
        assert client.patch(url, json=patch, headers=ana).status_code == 422
    assert client.get(url, headers=ana).json()['texto'] == 'Minha opinião'
    edit = client.patch(url, json={'texto': 'Outra opinião'}, headers=ana).json()
    assert edit['musica']['id'] == 1 and edit['created_at'] == a['created_at']
    same = client.patch(url, json={'texto': ' Outra opinião '}, headers=ana).json()
    assert same['edited_at'] == edit['edited_at']
    assert client.delete(url, headers=ana).status_code == 204
    assert client.get(url, headers=bia).status_code == 404
    nova = criar(client, ana).json()
    assert nova['id'] != a['id']
    with SessionLocal() as db:
        antiga = db.get(Post, a['id'])
        assert antiga.texto == '' and antiga.deleted_at is not None
        assert antiga.autor_id == a['autor']['id']
    perfil = client.get('/usuarios/ana/posts', headers=ana).json()
    assert perfil['total'] == 2
    assert all(p['id'] != a['id'] for p in perfil['items'])


def test_posts_validacao_e_sessao(client, logar):
    assert client.post('/posts', json={'texto': 'oi'}).status_code == 401
    ana = logar('ana')
    for dados in [{'texto': ' '}, {'texto': 'x' * 3001}, {'texto': 'oi', 'autor_id': 20}]:
        assert client.post('/posts', json=dados, headers=ana).status_code == 422
    with SessionLocal() as db:
        assert list(db.scalars(select(Post))) == []


def test_reviews_concorrentes_conexoes_independentes(client, logar):
    ana = logar('ana')
    popular()
    autor_id = client.get('/auth/eu', headers=ana).json()['id']
    barreira = Barrier(2)
    def publicar(_):
        with SessionLocal() as db:
            barreira.wait(timeout=5)
            try:
                return 201, posts.criar(db, PostCreate(texto='Review', musica_id=1), autor_id).id
            except HTTPException as e:
                return e.status_code, e.detail['post_id']
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(publicar, range(2)))
    assert sorted(r[0] for r in resultados) == [201, 409]
    assert resultados[0][1] == resultados[1][1]
    with SessionLocal() as db:
        assert len(list(db.scalars(select(Post).where(Post.deleted_at.is_(None))))) == 1
