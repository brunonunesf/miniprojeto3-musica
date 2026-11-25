import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reset_demo import ErroReset, resetar_demo, verificar_alvo


def construir(caminho, valor='inicial'):
    with sqlite3.connect(caminho) as db:
        db.execute('create table exemplo (valor text)')
        db.execute('insert into exemplo values (?)', (valor,))


def ler(caminho):
    with sqlite3.connect(caminho) as db:
        return db.execute('select valor from exemplo').fetchall()


def reset(alvo, callback=construir, **kwargs):
    return resetar_demo(alvo, alvo, callback, confirmar=True, aplicacao_parada=True, **kwargs)


def test_backup_preserva_ensaio_e_reconstroi_cenario(tmp_path):
    alvo = tmp_path / 'issue13.db'
    construir(alvo, 'editado no ensaio')
    backup = reset(alvo)
    assert ler(alvo) == [('inicial',)]
    assert ler(backup) == [('editado no ensaio',)]
    assert backup.parent == alvo.parent
    assert not list(tmp_path.glob('.issue13-novo-*'))


def test_primeira_preparacao_sem_backup(tmp_path):
    alvo = tmp_path / 'issue13.db'
    assert reset(alvo) is None
    assert ler(alvo) == [('inicial',)]


def test_falha_preparacao_preserva_original(tmp_path):
    alvo = tmp_path / 'issue13.db'
    construir(alvo, 'original')
    def falhar(novo):
        construir(novo)
        raise ValueError('validação semântica falhou')
    with pytest.raises(ValueError):
        reset(alvo, falhar)
    assert ler(alvo) == [('original',)]
    assert not list(tmp_path.glob('.issue13-novo-*'))


def test_falha_backup_preserva_original(tmp_path, monkeypatch):
    import reset_demo
    alvo = tmp_path / 'issue13.db'
    construir(alvo, 'original')
    def falhar(*args):
        raise OSError('sem espaço')
    monkeypatch.setattr(reset_demo, 'backup_sqlite', falhar)
    with pytest.raises(OSError):
        reset(alvo)
    assert ler(alvo) == [('original',)]


def test_confirmacoes_obrigatorias(tmp_path):
    alvo = tmp_path / 'issue13.db'
    for confirmar, parado in [(False,False),(True,False),(False,True)]:
        with pytest.raises(ErroReset):
            resetar_demo(alvo, alvo, construir, confirmar=confirmar, aplicacao_parada=parado)
    assert not alvo.exists()


def test_recusa_outro_caminho_e_symlink(tmp_path):
    alvo = tmp_path / 'issue13.db'
    outro = tmp_path / 'pessoal.db'
    construir(outro)
    with pytest.raises(ErroReset):
        verificar_alvo(outro, alvo)
    alvo.symlink_to(outro)
    with pytest.raises(ErroReset):
        reset(alvo)
    assert ler(outro) == [('inicial',)]


def test_recusa_wal_e_mudanca_durante_preparacao(tmp_path):
    alvo = tmp_path / 'issue13.db'
    construir(alvo, 'original')
    wal = Path(str(alvo) + '-wal')
    wal.touch()
    with pytest.raises(ErroReset):
        reset(alvo)
    wal.unlink()
    def alterar(novo):
        construir(novo)
        with sqlite3.connect(alvo) as db:
            db.execute("update exemplo set valor='mudou'")
    with pytest.raises(ErroReset):
        reset(alvo, alterar)
    assert ler(alvo) == [('mudou',)]


def test_integridade_referencial_antes_de_substituir(tmp_path):
    alvo = tmp_path / 'issue13.db'
    construir(alvo, 'original')
    def invalido(novo):
        with sqlite3.connect(novo) as db:
            db.executescript('create table pai(id integer primary key); create table filho(pai integer references pai(id)); insert into filho values (99);')
    with pytest.raises(ErroReset):
        reset(alvo, invalido)
    assert ler(alvo) == [('original',)]


def test_falha_replace_mantem_banco_e_backup(tmp_path, monkeypatch):
    import reset_demo
    alvo = tmp_path / 'issue13.db'
    construir(alvo, 'original')
    def falhar(*args):
        raise OSError('replace recusado')
    monkeypatch.setattr(reset_demo.os, 'replace', falhar)
    with pytest.raises(OSError):
        reset(alvo)
    assert ler(alvo) == [('original',)]
    assert ler(next(tmp_path.glob('issue13-backup-*.db'))) == [('original',)]
