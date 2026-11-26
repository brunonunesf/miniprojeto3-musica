"""Reconstrução SQLite com validação prévia e backup; sem conhecer modelos da API."""
import os
from contextlib import closing
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


class ErroReset(RuntimeError):
    pass


def verificar_alvo(alvo: Path, permitido: Path) -> Path:
    alvo = Path(os.path.abspath(alvo))
    permitido = Path(os.path.abspath(permitido))
    if alvo != permitido or any(p.is_symlink() for p in (alvo, *alvo.parents)):
        raise ErroReset('Reset restrito ao banco exclusivo de demo, sem links simbólicos')
    if alvo.exists() and (not alvo.is_file() or alvo.stat().st_nlink != 1):
        raise ErroReset('Banco deve ser arquivo regular sem hard links')
    verificar_inativo(alvo)
    return alvo


def verificar_inativo(alvo):
    # Não substituir o arquivo principal com journal/WAL separado: pode perder dados.
    if any(Path(str(alvo) + sufixo).exists() for sufixo in ('-wal', '-shm', '-journal')):
        raise ErroReset('Feche a aplicação e conclua checkpoint/journal antes do reset')


def integridade(alvo):
    with closing(sqlite3.connect(alvo.as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ErroReset('Banco SQLite inconsistente')
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ErroReset('Referências inválidas no banco SQLite')


def assinatura(alvo):
    if not alvo.exists():
        return None
    s = alvo.stat()
    return s.st_ino, s.st_size, s.st_mtime_ns


def backup_sqlite(origem, destino):
    with closing(sqlite3.connect(origem.as_uri() + '?mode=ro', uri=True)) as fonte:
        with closing(sqlite3.connect(destino)) as copia:
            fonte.backup(copia)
    integridade(destino)


def sincronizar(alvo):
    with alvo.open('rb') as arquivo:
        os.fsync(arquivo.fileno())


def resetar_demo(alvo: Path, permitido: Path, preparar_validar: Callable[[Path], None],
                 *, confirmar=False, aplicacao_parada=False):
    """Callback deve construir, validar semanticamente e FECHAR todas as conexões.

    Retorna caminho do backup (ou None na primeira preparação). Nunca remove backups.
    A declaração de aplicação parada é obrigatória; não detecta processos externos.
    """
    if not confirmar or not aplicacao_parada:
        raise ErroReset('Exige --confirmar-reset e --aplicacao-parada')
    alvo = verificar_alvo(alvo, permitido)
    inicial = assinatura(alvo)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    fd, nome = tempfile.mkstemp(prefix='.issue13-novo-', suffix='.db', dir=alvo.parent)
    os.close(fd)
    novo = Path(nome)
    backup = None
    try:
        preparar_validar(novo)
        verificar_inativo(novo)
        integridade(novo)
        sincronizar(novo)
        verificar_alvo(alvo, permitido)
        if assinatura(alvo) != inicial:
            raise ErroReset('Banco mudou durante a preparação; reset cancelado')
        if inicial is not None:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            fd, nome = tempfile.mkstemp(prefix=f'issue13-backup-{stamp}-', suffix='.db', dir=alvo.parent)
            os.close(fd)
            backup = Path(nome)
            try:
                backup_sqlite(alvo, backup)
                sincronizar(backup)
            except Exception:
                backup.unlink(missing_ok=True)
                raise
        verificar_alvo(alvo, permitido)
        if assinatura(alvo) != inicial:
            raise ErroReset('Banco mudou durante o backup; reset cancelado')
        os.replace(novo, alvo)
        return backup
    finally:
        for caminho in (novo, *(Path(str(novo) + s) for s in ('-wal', '-shm', '-journal'))):
            caminho.unlink(missing_ok=True)
