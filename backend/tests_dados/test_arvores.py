"""Contrato da #41, isolado de servidor, banco e conftest da API."""
from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.core.arvores import (
    EstruturaInvalida, FlorestaReviews, NoInexistente, ParametroInvalido,
    RegistroReview,
)
from cenarios_demo import preparar_cenario


def no(id, pai=None, musica='m', autor=None, apagada=False):
    return RegistroReview(id, musica, id if autor is None else autor, pai, apagada)


def ids(pagina):
    return [(p.no.review_id, p.distancia) for p in pagina.itens]


@pytest.fixture
def floresta():
    f = FlorestaReviews()
    f.reconstruir([no('a'), no('b', 'a'), no('c', 'b'), no('d', 'a'),
                   no('e', 'd'), no('outra'), no('outra-musica', musica='x')])
    return f


def test_corrente_ramos_raizes_e_ordens(floresta):
    f = floresta
    assert ids(f.descendentes('a')) == [('b', 1), ('d', 1), ('c', 2), ('e', 2)]
    assert ids(f.descendentes('a', ordem='dfs')) == [('b', 1), ('c', 2), ('d', 1), ('e', 2)]
    assert ids(f.ancestrais('c')) == [('b', 1), ('a', 2)]
    assert f.pai('c') == f.consultar('b')
    assert f.pai('a') is None
    assert f.raiz('c') == f.consultar('a')
    assert [n.review_id for n in f.raizes('m')] == ['a', 'outra']
    assert [n.review_id for n in f.raizes('x')] == ['outra-musica']
    assert f.raizes('ausente') == ()
    assert not f.descendentes('outra').itens
    assert not f.ancestrais('outra').itens


def test_apagada_preserva_nivel_autor_e_descendentes(floresta):
    f = floresta
    antes = ids(f.descendentes('a'))
    f.marcar_apagada('b')
    f.marcar_apagada('a')
    assert f.marcar_apagada('b') == f.consultar('b')
    assert ids(f.descendentes('a')) == antes
    assert ids(f.ancestrais('c')) == [('b', 1), ('a', 2)]
    assert all(p.no.apagada for p in f.ancestrais('c').itens)
    assert f.consultar('b').autor_id == 'b'
    assert f.raiz('c').apagada
    f.inserir(no('nova', autor='a'))
    assert f.raiz('nova').review_id == 'nova'
    assert f.raiz('c').review_id == 'a'
    with pytest.raises(EstruturaInvalida):
        f.inserir(no('filho-novo', 'b'))


def test_reconstrucao_fora_de_ordem_e_referencia_apagada():
    f = FlorestaReviews()
    f.reconstruir([no('c', 'b'), no('d', 'a'), no('b', 'a', apagada=True), no('a')])
    assert ids(f.descendentes('a')) == [('d', 1), ('b', 1), ('c', 2)]
    assert ids(f.ancestrais('c')) == [('b', 1), ('a', 2)]


@pytest.mark.parametrize('registros', [
    [no('a'), no('a')], [no('a', 'ausente')],
    [no('a'), no('b', 'a', musica='outra')], [no('a', 'a')],
    [no('a', 'b'), no('b', 'a')],
    [no('raiz'), no('a', 'b', apagada=True), no('b', 'a')],
])
def test_reconstrucao_invalida_nao_substitui_estado(floresta, registros):
    antes = floresta.descendentes('a')
    with pytest.raises(EstruturaInvalida):
        floresta.reconstruir(registros)
    assert floresta.descendentes('a') == antes
    assert floresta.raiz('c').review_id == 'a'


def test_iterador_com_falha_tambem_preserva_estado(floresta):
    def registros():
        yield no('nova')
        raise RuntimeError('falha na leitura')
    with pytest.raises(RuntimeError):
        floresta.reconstruir(registros())
    assert floresta.consultar('a').origem_id is None
    with pytest.raises(NoInexistente):
        floresta.consultar('nova')


@pytest.mark.parametrize('registro', [no('a'), no('a', 'a'), no('z', 'ausente'), no('z', 'a', musica='x')])
def test_insercao_invalida_atomica(floresta, registro):
    antes = floresta.descendentes('a')
    with pytest.raises(EstruturaInvalida):
        floresta.inserir(registro)
    assert floresta.descendentes('a') == antes
    with pytest.raises(NoInexistente):
        floresta.consultar('z')


def test_insercao_ordem_identidade_e_imutabilidade(floresta):
    f = floresta
    f.inserir(no(1, 'a'))
    f.inserir(no('1', 'a'))
    assert ids(f.descendentes('a', profundidade_maxima=1))[-2:] == [(1, 1), ('1', 1)]
    with pytest.raises(FrozenInstanceError):
        f.consultar('a').origem_id = 'c'
    with pytest.raises(FrozenInstanceError):
        f.descendentes('a').tem_mais = True
    raizes = f.raizes('m')
    raizes += (no('externo'),)
    assert len(f.raizes('m')) == 2
    assert not hasattr(f, 'curtir') and not hasattr(f, 'comentar')


@pytest.mark.parametrize('metodo', ['ancestrais', 'descendentes'])
@pytest.mark.parametrize('parametros', [
    {'offset': -1}, {'offset': True}, {'offset': 1.5},
    {'limit': 0}, {'limit': 201}, {'limit': False}, {'limit': '50'},
    {'profundidade_maxima': -1}, {'profundidade_maxima': True},
    {'profundidade_maxima': 1.5},
])
def test_limites_invalidos(floresta, metodo, parametros):
    with pytest.raises(ParametroInvalido):
        getattr(floresta, metodo)('a', **parametros)


def test_paginas_e_profundidade(floresta):
    f = floresta
    assert ids(f.descendentes('a', limit=2)) == [('b', 1), ('d', 1)]
    assert f.descendentes('a', limit=2).tem_mais
    assert ids(f.descendentes('a', offset=2, limit=2)) == [('c', 2), ('e', 2)]
    assert not f.descendentes('a', offset=2, limit=2).tem_mais
    assert not f.descendentes('a', offset=40).itens
    assert not f.descendentes('a', profundidade_maxima=0).tem_mais
    assert not f.ancestrais('c', profundidade_maxima=0).itens
    assert ids(f.ancestrais('c', limit=1)) == [('b', 1)]
    assert f.ancestrais('c', limit=1).tem_mais
    assert ids(f.ancestrais('c', offset=1, limit=1)) == [('a', 2)]
    assert not f.ancestrais('c', offset=1, limit=1).tem_mais
    for ordem in ('bfs', 'dfs'):
        pagina = f.descendentes('a', ordem=ordem, profundidade_maxima=1, offset=1, limit=1)
        assert ids(pagina) == [('d', 1)]
        assert not pagina.tem_mais


def test_corrente_profunda_e_paginas_padrao():
    f = FlorestaReviews()
    tamanho = sys.getrecursionlimit() + 100
    f.reconstruir(no(i, i - 1 if i else None) for i in reversed(range(tamanho)))
    assert f.raiz(tamanho - 1).review_id == 0
    for ordem in ('bfs', 'dfs'):
        assert len(f.descendentes(0, ordem=ordem).itens) == 50
        pagina = f.descendentes(0, ordem=ordem, offset=tamanho - 201, limit=200)
        assert len(pagina.itens) == 200
        assert pagina.itens[-1].no.review_id == tamanho - 1
        assert not pagina.tem_mais
    assert len(f.ancestrais(tamanho - 1, limit=200).itens) == 200
    assert f.ancestrais(tamanho - 1, offset=tamanho).itens == ()


def test_vazia_inexistentes_e_reconstrucao_vazia(floresta):
    floresta.reconstruir([])
    assert floresta.raizes('m') == ()
    for metodo in ('consultar', 'pai', 'raiz', 'marcar_apagada', 'ancestrais', 'descendentes'):
        with pytest.raises(NoInexistente):
            getattr(floresta, metodo)('ausente')
    with pytest.raises(ParametroInvalido):
        floresta.descendentes('ausente', ordem='incorreta')


def test_ordem_invalida(floresta):
    with pytest.raises(ParametroInvalido):
        floresta.descendentes('a', ordem='incorreta')


@pytest.mark.parametrize('id', [True, None, 1.5, [], {}])
def test_identificadores_sem_coercao(id):
    with pytest.raises(ParametroInvalido):
        no(id)
    with pytest.raises(ParametroInvalido):
        FlorestaReviews().consultar(id)


def test_cenario_issue13_sem_adapter_ou_banco():
    cenario = preparar_cenario()
    f = FlorestaReviews()
    registros = [RegistroReview(p['chave'], p['musica'], p['autor'], p['origem'])
                 for p in cenario['posts']]
    f.reconstruir(registros)
    assert ids(f.descendentes('review-001')) == [
        ('review-002', 1), ('review-004', 1), ('review-003', 2)]
    antes = f.descendentes('review-001')
    # Likes são outro conjunto de dados; não fazem parte da entrada da floresta.
    cenario['likes'].clear()
    f.reconstruir(registros)
    assert f.descendentes('review-001') == antes
    assert sum(len(f.raizes(m['chave_catalogo'])) for m in cenario['musicas']) == 47


def test_importacao_sem_framework_ou_banco():
    codigo = """
import sys
from app.core.arvores import FlorestaReviews, RegistroReview
f = FlorestaReviews()
f.inserir(RegistroReview(1, 'musica', 1))
assert not any(n.split('.')[0] in {'fastapi', 'sqlalchemy', 'app.db'} for n in sys.modules)
assert 'app.db' not in sys.modules
"""
    subprocess.run([sys.executable, '-c', codigo], cwd=BACKEND, check=True)
