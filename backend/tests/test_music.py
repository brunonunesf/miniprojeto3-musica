import json
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from app.db import SessionLocal
from app.models.music import Music
from app.models.user import User
from app.schemas.music import MusicData

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from seed_music import seed_musicas, CATALOGO


def popular():
    with SessionLocal() as db:
        return seed_musicas(db)


def test_catalogo_auth_busca_e_identidades(client, logar):
    headers = logar('ana')
    assert popular() == 6
    assert client.get('/musicas').status_code == 401
    assert client.get('/musicas/1').status_code == 401
    resposta = client.get('/musicas?q=  HORIZONTE  &limit=2', headers=headers).json()
    assert resposta['total'] == 5
    assert len(resposta['items']) == 2
    assert client.get('/musicas?offset=2&limit=2', headers=headers).json()['offset'] == 2
    items = client.get('/musicas?q=aurora', headers=headers).json()['items']
    assert {m['tipo_versao'] for m in items} == {'original', 'remix', 'ao_vivo', 'remaster'}
    assert len({m['id'] for m in items}) == 4
    assert client.get('/musicas?q=lua MARÉ', headers=headers).json()['total'] == 1
    assert client.get('/musicas?q=inexistente', headers=headers).json()['items'] == []
    m = items[0]
    assert client.get(f"/musicas/{m['id']}", headers=headers).json() == m
    assert client.get('/musicas/99999', headers=headers).status_code == 404
    for path in ['/musicas/0', '/musicas?limit=101', '/musicas?offset=-1', '/musicas?limit=0']:
        assert client.get(path, headers=headers).status_code == 422


def test_seed_idempotente_preserva_usuarios(client, logar):
    logar('ana')
    assert popular() == 6
    with SessionLocal() as db:
        ids = list(db.scalars(select(Music.id).order_by(Music.id)))
        assert seed_musicas(db) == 0
        assert list(db.scalars(select(Music.id).order_by(Music.id))) == ids
        assert db.scalar(select(func.count()).select_from(User)) == 1


def test_catalogo_invalido_nao_grava(client, tmp_path):
    rows = json.loads(CATALOGO.read_text())
    arquivo = tmp_path / 'musicas.json'
    arquivo.write_text(json.dumps(rows + [rows[0]]))
    with SessionLocal() as db:
        with pytest.raises(ValueError, match='repetida'):
            seed_musicas(db, arquivo)
        assert db.scalar(select(func.count()).select_from(Music)) == 0
    for campo, valor in [('titulo', '  '), ('artista', ''), ('generos', [' ']), ('tags', []), ('tipo_versao', 'outra')]:
        with pytest.raises(ValidationError):
            MusicData.model_validate({**rows[0], campo: valor})
