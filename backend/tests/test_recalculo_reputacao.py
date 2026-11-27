"""Aceite #51: reconstrução retroativa e indisponibilidade recuperável, com banco real."""
from sqlalchemy import select

from app.core.arvores import ErroArvore
from app.core.reputacao import ErroReputacao, EventoCurtida, EventoDerivada, reputacao_reviews
from app.db import SessionLocal
from app.models.evento_reputacao import EventoReputacao
from app.models.post import Post
from app.models.review_apagada import ReviewApagada
from app.services import arvores, reputacao
from tests.test_reputacao_api import criar, refazer_tudo_como_no_reinicio
from tests.test_trocar_origem import cenario, trocar


def conferir_referencia():
    """Oráculo independente: percorre registros do banco, sem chamar o cálculo do core."""
    with SessionLocal() as db:
        registros = list(db.scalars(select(Post))) + list(db.scalars(select(ReviewApagada)))
        nos = {r.id: (r.autor_id, r.origem_id) for r in registros}
        totais = {}
        eventos = list(db.scalars(select(EventoReputacao)))
        for e in eventos:
            autor, pai = nos[e.review_id]
            creditos = {}
            if e.tipo == 'curtida' and e.usuario_id == autor:
                creditos = {autor: 1}
            else:
                atual = e.review_id if e.tipo == 'curtida' else pai
                for pontos in (4, 2, 1):
                    if atual is None:
                        break
                    a, atual = nos[atual]
                    creditos[a] = max(creditos.get(a, 0), pontos)
            evento = EventoCurtida(e.review_id, e.usuario_id) if e.tipo == 'curtida' else EventoDerivada(e.review_id)
            assert reputacao_reviews.contribuicoes(evento) == creditos
            for a, pontos in creditos.items():
                totais[a] = totais.get(a, 0) + pontos
        assert reputacao_reviews.totais() == totais
        return sorted(e.chave for e in eventos), totais


def falhar(*args, **kwargs):
    raise ErroReputacao('falha injetada')


def test_recalculo_completo_bate_com_oraculo_por_evento(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    leitor = logar('leitor')
    for nome in ('pedro', 'caio'):
        client.post(f"/posts/{r[nome]['id']}/curtir", headers=leitor)
    client.post(f"/posts/{r['pedro']['id']}/curtir", headers=p['pedro'])
    # Uma curtida desfeita não deve reaparecer depois da movimentação.
    client.post(f"/posts/{r['julia']['id']}/curtir", headers=leitor)
    client.delete(f"/posts/{r['julia']['id']}/curtir", headers=leitor)
    # Descendente apagado mantém sua derivação e a curtida histórica.
    client.delete(f"/posts/{r['caio']['id']}", headers=p['caio'])
    eventos, antes = conferir_referencia()
    for destino in ('bia', 'ana', 'julia', 'julia'):
        resposta = trocar(client, p['pedro'], r['pedro']['id'], r[destino]['id'])
        assert resposta.status_code == 200
        assert resposta.json()['reputacao_disponivel'] is True
        assert conferir_referencia()[0] == eventos
    assert reputacao_reviews.totais() == antes
    trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
    client.delete(f"/posts/{r['pedro']['id']}/curtir", headers=leitor)
    conferir_referencia()  # descurtir usa os créditos da corrente nova
    refazer_tudo_como_no_reinicio()
    conferir_referencia()


def test_autor_repetido_e_ancestrais_compartilhados(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    # Ana pode publicar de novo depois de apagar sua raiz; a referência mantém autoria.
    client.delete(f"/posts/{r['ana']['id']}", headers=p['ana'])
    nova = criar(client, p['ana'], id_da_musica, texto='voltei', origem_id=r['julia']['id'])
    client.post(f"/posts/{nova['id']}/curtir", headers=p['bia'])
    eventos, antes = conferir_referencia()
    # A curtida começa em Ana → Júlia → Ana: Ana fica com 4, não 5.
    for destino in ('caio', 'bia', 'julia'):
        resposta = trocar(client, p['ana'], nova['id'], r[destino]['id'])
        assert resposta.status_code == 200
        assert conferir_referencia()[0] == eventos
    assert reputacao_reviews.totais() == antes


def test_origem_salva_pontos_ocultos_e_recuperacao_na_consulta(client, logar, id_da_musica, monkeypatch):
    p, r = cenario(client, logar, id_da_musica)
    eventos, antigos = conferir_referencia()
    with monkeypatch.context() as m:
        m.setattr(reputacao_reviews, 'reconstruir', falhar)
        resposta = trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
        assert resposta.status_code == 200
        assert resposta.json()['origem_id'] == r['bia']['id']
        assert resposta.json()['reputacao_disponivel'] is False
        assert reputacao_reviews.totais() == antigos  # snapshot anterior preservado internamente
        for nome in p:
            perfil = client.get(f'/usuarios/{nome}', headers=p['ana'])
            assert perfil.status_code == 200
            assert perfil.json()['reputacao'] is None
        with SessionLocal() as db:
            assert db.get(Post, r['pedro']['id']).origem_id == r['bia']['id']
            assert sorted(db.scalars(select(EventoReputacao.chave))) == eventos
    assert client.get('/usuarios/bia', headers=p['ana']).json()['reputacao'] is not None
    conferir_referencia()


def test_repetir_origem_atual_recupera_sem_duplicar(client, logar, id_da_musica, monkeypatch):
    p, r = cenario(client, logar, id_da_musica)
    eventos, _ = conferir_referencia()
    with monkeypatch.context() as m:
        m.setattr(reputacao_reviews, 'reconstruir', falhar)
        trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
    resposta = trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
    assert resposta.json()['reputacao_disponivel'] is True
    assert conferir_referencia()[0] == eventos


def test_falha_da_arvore_nao_calcula_sobre_floresta_anterior(client, logar, id_da_musica, monkeypatch):
    p, r = cenario(client, logar, id_da_musica)
    def arvore_falha(*args):
        raise ErroArvore('falha da árvore')
    with monkeypatch.context() as m:
        m.setattr(arvores, 'reconstruir', arvore_falha)
        m.setattr(reputacao_reviews, 'reconstruir', lambda *args: (_ for _ in ()).throw(AssertionError('árvore antiga usada')))
        resposta = trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
        assert resposta.json()['reputacao_disponivel'] is False
        assert client.get('/usuarios/ana', headers=p['ana']).json()['reputacao'] is None
    client.get('/usuarios/ana', headers=p['ana'])
    conferir_referencia()


def test_interacoes_durante_pendencia_nao_liberam_acumulador_parcial(client, logar, id_da_musica, monkeypatch):
    p, r = cenario(client, logar, id_da_musica)
    leitor = logar('leitor')
    with monkeypatch.context() as m:
        m.setattr(reputacao_reviews, 'reconstruir', falhar)
        trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
        assert client.post(f"/posts/{r['pedro']['id']}/curtir", headers=leitor).status_code == 200
        assert client.delete(f"/posts/{r['pedro']['id']}/curtir", headers=leitor).status_code == 200
        criar(client, leitor, id_da_musica, texto='derivada', origem_id=r['pedro']['id'])
        assert client.get('/usuarios/ana', headers=p['ana']).json()['reputacao'] is None
    client.get('/usuarios/ana', headers=p['ana'])
    conferir_referencia()


def test_startup_com_falha_nao_expoe_memoria_da_execucao_anterior(client, logar, id_da_musica, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    p, r = cenario(client, logar, id_da_musica)
    with monkeypatch.context() as m:
        m.setattr(reputacao_reviews, 'reconstruir', falhar)
        with TestClient(app) as reiniciado:
            assert reiniciado.get('/usuarios/ana', headers=p['ana']).json()['reputacao'] is None
    assert client.get('/usuarios/ana', headers=p['ana']).json()['reputacao'] is not None
    conferir_referencia()


def test_falha_transitoria_recupera_na_segunda_tentativa(client, logar, id_da_musica, monkeypatch):
    p, r = cenario(client, logar, id_da_musica)
    original = reputacao_reviews.reconstruir
    chamadas = 0
    def uma_falha(*args):
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            raise ErroReputacao('transitória')
        return original(*args)
    monkeypatch.setattr(reputacao_reviews, 'reconstruir', uma_falha)
    resposta = trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
    assert resposta.json()['reputacao_disponivel'] is True
    assert chamadas == 2
    conferir_referencia()


def test_falha_de_leitura_do_banco_preserva_origem_e_oculta_pontos(client, logar, id_da_musica, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    p, r = cenario(client, logar, id_da_musica)
    def banco_falha(*args):
        raise SQLAlchemyError('leitura indisponível')
    with monkeypatch.context() as m:
        m.setattr(arvores, 'reconstruir', banco_falha)
        resposta = trocar(client, p['pedro'], r['pedro']['id'], r['bia']['id'])
        assert resposta.status_code == 200
        assert resposta.json()['origem_id'] == r['bia']['id']
        assert resposta.json()['reputacao_disponivel'] is False
        assert client.get('/usuarios/ana', headers=p['ana']).json()['reputacao'] is None
    client.get('/usuarios/ana', headers=p['ana'])
    conferir_referencia()
