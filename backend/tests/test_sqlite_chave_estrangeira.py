"""Guarda: nenhum teste pode deixar uma conexão do pool com a chave estrangeira desligada.

O SQLite só confere chave estrangeira se for pedido, e por conexão. Um teste que desliga o `PRAGMA`
numa `Session` pode religar em outra conexão (a `Session` devolve a conexão ao pool no `commit()`) e
deixar uma desligada, o que faz testes seguintes passarem ou falharem conforme a conexão que pegam.
Este arquivo roda depois dos demais (ordem alfabética) justamente para pegar esse vazamento.
"""

from sqlalchemy import text

from app.db import SessionLocal


def test_todas_as_conexoes_do_pool_tem_a_chave_estrangeira_ligada(client):
    sessoes = [SessionLocal() for _ in range(12)]  # segura todas ao mesmo tempo: pega o pool inteiro
    try:
        estados = [s.execute(text("PRAGMA foreign_keys")).scalar() for s in sessoes]
    finally:
        for s in sessoes:
            s.close()

    assert estados == [1] * 12
