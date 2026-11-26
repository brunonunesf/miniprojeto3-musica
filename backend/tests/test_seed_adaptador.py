"""Integração do mapeamento do #74; fixtures sem origens não são carga de produção."""
import copy
from collections import Counter
from pathlib import Path

import pytest
from sqlalchemy import select, text

from app.db import SessionLocal, Base, engine
from app.models.user import User
from app.models.post import Post
from app.models.musica import Musica
from app.services.demo_seed import criar_adaptador
from cenarios_demo import preparar_cenario
from seed_demo import IntegracaoPendente, seed_fake, SENHA_DEMO, cargas


@pytest.fixture(autouse=True)
def limpar_marca_de_fixture():
    # Base.metadata.drop_all do client não inclui a tabela operacional do seed.
    cargas.drop(engine, checkfirst=True)
    yield
    cargas.drop(engine, checkfirst=True)


@pytest.fixture
def catalogo_demo(monkeypatch):
    monkeypatch.setenv('CATALOGO_MUSICAL_PATH', 'data/musicas_demo.json')


@pytest.fixture
def fixture_raizes(catalogo_demo, monkeypatch):
    cenario = preparar_cenario()
    cenario['versao'] = 'fixture-teste-raizes-v2'
    for post in cenario['posts']:
        post['origem'] = None
    # Só testes trocam a entrada; não existe flag de bypass no produto.
    monkeypatch.setattr('seed_demo.preparar_cenario', lambda: copy.deepcopy(cenario))
    return cenario


def login(client, username='bruno_nunes'):
    r = client.post('/auth/login', json={'username': username, 'password': SENHA_DEMO})
    assert r.status_code == 200
    return {'Authorization': 'Bearer ' + r.json()['token']}


def aplicar_fixture():
    with SessionLocal() as db:
        return seed_fake(db)


def test_carga_completa_falha_sem_origens_e_sem_marca(catalogo_demo, client):
    with SessionLocal() as db:
        with pytest.raises(IntegracaoPendente, match='origens da #10'):
            seed_fake(db)
        assert list(db.scalars(select(User))) == []
        assert list(db.scalars(select(Post))) == []
        assert not db.scalar(text("select count(*) from sqlite_master where name='demo_seed_cargas'"))


def test_mapeamento_api_ranking_reinicio_e_preservacao(fixture_raizes, client):
    from fastapi.testclient import TestClient
    from app.main import app

    aplicar_fixture()
    h = login(client)
    for username in ('cecilia_candeia', 'daniel_dantas', 'ryan_rodrigues'):
        login(client, username)
    lista = client.get('/musicas?limit=100', headers=h).json()
    assert lista['total'] == 20
    assert 'password_hash' not in str(client.get('/usuarios/bruno_nunes', headers=h).json())
    ids = {m['chave_catalogo']: m['id'] for m in lista['items']}
    ranking = client.get('/musicas/populares?limit=100', headers=h).json()
    esperadas = Counter(p['musica'] for p in fixture_raizes['posts'])
    assert ranking['total'] == 18
    assert [(m['id'], m['quantidade_reviews']) for m in ranking['items']] == sorted(
        [(ids[chave], n) for chave, n in esperadas.items()], key=lambda par: (-par[1], par[0]))
    assert all(m['titulo'] not in ('Evidências', 'Dias De Luta, Dias De Gloria') for m in ranking['items'])
    assert client.get('/musicas?q=Anjos', headers=h).json()['total'] == 1
    assert client.get('/feed', headers=h).json()['total'] > 0
    assert client.get('/usuarios/ryan_rodrigues/posts', headers=h).json()['total'] == 0
    # O teste opera com IDs reais retornados pelo banco e APIs.
    posts = client.get('/usuarios/bruno_nunes/posts?limit=100', headers=h).json()['items']
    editar, apagar = posts[:2]
    assert client.patch(f"/posts/{editar['id']}", headers=h, json={'nota': 9, 'texto': 'Ensaio preservado'}).status_code == 200
    assert client.get('/musicas/populares?limit=100', headers=h).json() == ranking
    likes = fixture_raizes['likes'][0]
    with SessionLocal() as db:
        ref = next(p for p in fixture_raizes['posts'] if p['chave'] == likes['post'])
        autor = db.scalar(select(User).where(User.username == ref['autor']))
        review_id = db.scalar(select(Post.id).where(Post.autor_id == autor.id, Post.musica_id == ids[ref['musica']]))
    hl = login(client, likes['usuario'])
    assert client.delete(f'/posts/{review_id}/curtir', headers=hl).status_code == 200
    follow = fixture_raizes['follows'][0]
    hf = login(client, follow['seguidor'])
    assert client.delete(f"/usuarios/{follow['seguido']}/follow", headers=hf).status_code == 204
    assert client.delete(f"/posts/{apagar['id']}", headers=h).status_code == 204
    esperadas[apagar['musica']['chave_catalogo']] -= 1
    atual = client.get('/musicas/populares?limit=100', headers=h).json()['items']
    assert [(m['id'], m['quantidade_reviews']) for m in atual] == sorted(
        [(ids[chave], n) for chave, n in esperadas.items() if n], key=lambda par: (-par[1], par[0]))
    assert aplicar_fixture() == 'já aplicada; ações preservadas'
    with TestClient(app) as reinicio:
        assert reinicio.get('/musicas?limit=100', headers=h).json() == lista
        editada = reinicio.get(f"/posts/{editar['id']}", headers=h).json()
        assert editada['texto'] == 'Ensaio preservado'
        assert reinicio.get(f"/posts/{apagar['id']}", headers=h).status_code == 404
        if review_id != apagar['id']:
            assert reinicio.get(f'/posts/{review_id}', headers=hl).json()['curtido_por_mim'] is False
        assert reinicio.get(f"/usuarios/{follow['seguido']}", headers=hf).json()['eu_sigo'] is False


def test_validacao_semantica_falha_reverte_carga(fixture_raizes, client, monkeypatch):
    from app.services.demo_seed import AdaptadorBackend
    original = AdaptadorBackend.validar
    def falhar(self, db, cenario):
        original(self, db, cenario)
        raise ValueError('Falha semântica simulada')
    monkeypatch.setattr(AdaptadorBackend, 'validar', falhar)
    with SessionLocal() as db:
        with pytest.raises(ValueError, match='semântica'):
            seed_fake(db)
        assert list(db.scalars(select(User))) == []
        assert list(db.scalars(select(Post))) == []
        assert db.scalar(text('select count(*) from demo_seed_cargas')) == 0
    monkeypatch.setattr(AdaptadorBackend, 'validar', original)
    assert aplicar_fixture() == 'carga aplicada'


def test_preflight_colisao_preserva_usuario(fixture_raizes, client):
    from app.services.auth import gerar_hash
    with SessionLocal() as db:
        db.add(User(username='manual', name='Ensaio', password_hash=gerar_hash('outra-senha')))
        db.commit()
        with pytest.raises(IntegracaoPendente, match='Colisão'):
            seed_fake(db)
        assert [u.username for u in db.scalars(select(User))] == ['manual']
        assert list(db.scalars(select(Post))) == []


def test_schema_antigo_sem_autoincrement_e_recusado(fixture_raizes, tmp_path):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session
    antigo = create_engine('sqlite:///' + str(tmp_path / 'antigo.db'))
    @event.listens_for(antigo, 'connect')
    def fk(c, _):
        c.execute('PRAGMA foreign_keys=ON')
    try:
        Base.metadata.create_all(antigo)
        with antigo.begin() as c:
            ddl = c.scalar(text("select sql from sqlite_master where name='posts'"))
            c.execute(text('drop table posts'))
            c.execute(text(ddl.replace('AUTOINCREMENT', '')))
        with Session(antigo) as db:
            with pytest.raises(IntegracaoPendente, match='AUTOINCREMENT'):
                seed_fake(db)
            assert list(db.scalars(select(User))) == []
    finally:
        antigo.dispose()


def test_reset_com_modelos_reais_preserva_backup(fixture_raizes, tmp_path):
    import sqlite3
    from contextlib import closing
    from reset_demo import resetar_demo
    from seed_demo import preparar_validar_banco
    alvo = tmp_path / 'issue13.db'
    adaptador = criar_adaptador()
    callback = lambda caminho: preparar_validar_banco(caminho, adaptador)
    resetar_demo(alvo, alvo, callback, confirmar=True, aplicacao_parada=True)
    with closing(sqlite3.connect(alvo)) as db:
        db.execute("update posts set texto='editado no ensaio' where id=(select min(id) from posts)")
        db.commit()
    backup = resetar_demo(alvo, alvo, callback, confirmar=True, aplicacao_parada=True)
    with closing(sqlite3.connect(alvo)) as db:
        assert db.execute('select count(*) from posts').fetchone()[0] == 50
        assert db.execute("select count(*) from posts where texto='editado no ensaio'").fetchone()[0] == 0
        assert db.execute('select count(*) from curtidas').fetchone()[0] == 30
    with closing(sqlite3.connect(backup)) as db:
        assert db.execute("select count(*) from posts where texto='editado no ensaio'").fetchone()[0] == 1


def test_catalogo_diferente_nao_e_misturado(fixture_raizes, client, monkeypatch):
    monkeypatch.delenv('CATALOGO_MUSICAL_PATH')
    with SessionLocal() as db:
        with pytest.raises(IntegracaoPendente, match='Catálogo diferente'):
            seed_fake(db)
        assert len(list(db.scalars(select(Musica)))) == 20
        assert list(db.scalars(select(User))) == []
        assert list(db.scalars(select(Post))) == []


def test_preflight_rejeita_constraints_fk_ausentes(fixture_raizes, client):
    with engine.begin() as db:
        db.execute(text('drop table curtidas'))
        db.execute(text('create table curtidas (usuario_id integer, post_id integer, created_at datetime, primary key (usuario_id, post_id))'))
    with SessionLocal() as db:
        with pytest.raises(IntegracaoPendente, match='Chave estrangeira ausente: curtidas'):
            seed_fake(db)
        assert list(db.scalars(select(User))) == []


def test_preflight_nao_adota_interacoes_orfas_antigas(fixture_raizes, client):
    # FK ativa não corrige dados gravados antes de sua ativação.
    with engine.connect() as db:
        db.exec_driver_sql('PRAGMA foreign_keys=OFF')
        db.exec_driver_sql("insert into comentarios (autor_id, post_id, texto, created_at) values (999, 999, 'órfão anterior', CURRENT_TIMESTAMP)")
        db.commit()
        db.exec_driver_sql('PRAGMA foreign_keys=ON')
    with SessionLocal() as db:
        with pytest.raises(IntegracaoPendente, match='referências inválidas'):
            seed_fake(db)
        assert list(db.scalars(select(User))) == []
        assert list(db.scalars(select(Post))) == []
        assert db.scalar(text('select count(*) from comentarios')) == 1
