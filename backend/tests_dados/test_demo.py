import copy
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cenarios_demo import preparar_cenario, validar_cenario
from seed_demo import IntegracaoPendente, seed_fake


def test_cenario_reproduzivel_e_conta_nova():
    c = preparar_cenario()
    assert c == preparar_cenario()
    assert [p['origem'] for p in c['posts'][:5]] == [None, 'review-001', 'review-002', 'review-001', None]
    assert all('ryan_rodrigues' != p['autor'] for p in c['posts'])


def test_ciclos_e_duplicatas_rejeitados():
    c = preparar_cenario()
    c['posts'][0]['origem'] = 'review-003'
    with pytest.raises(ValueError):
        validar_cenario(c)
    c = preparar_cenario()
    c['posts'][5] = copy.deepcopy(c['posts'][0])
    with pytest.raises(ValueError):
        validar_cenario(c)


def test_sem_adaptador_nao_grava():
    engine = create_engine('sqlite://')
    with Session(engine) as db:
        with pytest.raises(IntegracaoPendente):
            seed_fake(db)
        assert db.execute(text("select name from sqlite_master where type='table'")).all() == []


class AdaptadorTeste:
    """Verifica apenas a orquestração, não simula entrega do backend."""
    def verificar(self, db, cenario):
        pass

    def gravar(self, db, cenario, senha):
        db.execute(text("insert into acoes values ('review', 'original'), ('like', 'ativo'), ('follow', 'ativo')"))


def test_reexecucao_preserva_edicao_exclusao_descurtida_unfollow():
    engine = create_engine('sqlite://')
    with Session(engine) as db:
        db.execute(text('create table acoes (tipo text, valor text)'))
        db.commit()
        seed_fake(db, AdaptadorTeste())
        db.execute(text("update acoes set valor='editado' where tipo='review'"))
        db.execute(text("delete from acoes where tipo in ('like', 'follow')"))
        db.commit()
        assert seed_fake(db) == 'já aplicada; ações preservadas'
        assert db.execute(text('select * from acoes')).all() == [('review', 'editado')]
        db.execute(text('delete from acoes'))
        db.commit()
        seed_fake(db)
        assert db.execute(text('select * from acoes')).all() == []


def test_rollback_e_nova_tentativa():
    class Falha(AdaptadorTeste):
        def gravar(self, db, cenario, senha):
            super().gravar(db, cenario, senha)
            raise ValueError('falha simulada')
    engine = create_engine('sqlite://')
    with Session(engine) as db:
        db.execute(text('create table acoes (tipo text, valor text)'))
        db.commit()
        with pytest.raises(ValueError):
            seed_fake(db, Falha())
        assert db.execute(text('select * from acoes')).all() == []
        seed_fake(db, AdaptadorTeste())
        assert db.execute(text('select count(*) from acoes')).scalar() == 3


def test_preflight_falha_sem_gravar():
    class Colisao(AdaptadorTeste):
        def verificar(self, db, cenario):
            raise ValueError('colisão de username')
    engine = create_engine('sqlite://')
    with Session(engine) as db:
        with pytest.raises(ValueError):
            seed_fake(db, Colisao())
        assert db.execute(text("select name from sqlite_master where type='table'")).all() == []


def test_referencias_spotify_correspondem_ao_catalogo():
    import json
    dados = Path(__file__).resolve().parents[1] / 'data'
    refs = json.loads((dados / 'referencias_spotify_demo.json').read_text())
    c = preparar_cenario()
    assert {r['chave_catalogo'] for r in refs} == {m['chave_catalogo'] for m in c['musicas']}
    assert len({r['spotify_id'] for r in refs}) == 20
    assert all(r['url'] == 'https://open.spotify.com/track/' + r['spotify_id'] for r in refs)


def test_cli_validacao_e_reset_preservam_banco(tmp_path):
    import os
    import subprocess
    backend = Path(__file__).resolve().parents[1]
    banco = tmp_path / 'pessoal.db'
    banco.write_bytes(b'nao apagar')
    env = dict(os.environ, DATABASE_URL=f'sqlite:///{banco}')
    comando = [sys.executable, str(backend / 'scripts/seed.py')]
    validar = subprocess.run(comando + ['--validar-demo'], env=env, capture_output=True, text=True)
    assert validar.returncode == 0
    for argumentos in [[], ['--reset-demo']]:
        resultado = subprocess.run(comando + argumentos, env=env, capture_output=True, text=True)
        assert resultado.returncode == 1
        assert banco.read_bytes() == b'nao apagar'


def test_carregamento_automatico_valida_contrato(monkeypatch):
    import seed_demo
    from types import SimpleNamespace
    class Completo(AdaptadorTeste):
        def preparar_banco(self, engine):
            pass
        def validar(self, db, cenario):
            pass
    adapter = Completo()
    monkeypatch.setattr(seed_demo, 'find_spec', lambda nome: object())
    monkeypatch.setattr(seed_demo, 'import_module', lambda nome: SimpleNamespace(criar_adaptador=lambda: adapter))
    assert seed_demo.carregar_adaptador() is adapter
    monkeypatch.setattr(seed_demo, 'import_module', lambda nome: SimpleNamespace(criar_adaptador=lambda: AdaptadorTeste()))
    with pytest.raises(IntegracaoPendente, match='preparar_banco'):
        seed_demo.carregar_adaptador()


def test_banco_temporario_exige_validacao_semantica(tmp_path):
    from seed_demo import preparar_validar_banco
    class Completo(AdaptadorTeste):
        def preparar_banco(self, engine):
            with engine.begin() as conexao:
                conexao.execute(text('create table acoes (tipo text, valor text)'))
        def validar(self, db, cenario):
            assert db.execute(text('select count(*) from acoes')).scalar() == 3
            raise ValueError('validação real rejeitou a carga')
    with pytest.raises(ValueError, match='validação real'):
        preparar_validar_banco(tmp_path / 'novo.db', Completo())
