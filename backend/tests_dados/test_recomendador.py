from dataclasses import replace
from datetime import datetime, timezone, timedelta
from math import log, sqrt
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.core.recomendador import (
    Curtida, EntradaInvalida, Musica, Recomendador, Review,
)

D = datetime(2026, 11, 26, tzinfo=timezone.utc)


def r(id, musica, autor=2, dias=0, **kw):
    return Review(id, musica, autor, D + timedelta(days=dias), **kw)


def chaves(saida):
    return [s.musica for s in saida]


def test_oraculo_independente_tfidf_e_explicacao():
    catalogo = [Musica('a', 'A', ('rock',)), Musica('b', 'B', ('rock',)),
                Musica('c', 'C', ('jazz',))]
    saida = Recomendador(catalogo).recomendar(1, [r(1, 'a', 1), r(2, 'b'), r(3, 'c')], [])
    comum, raro = log(4 / 3) + 1, log(4 / 2) + 1
    esperado = comum**2 / (comum**2 + raro**2)
    assert chaves(saida) == ['b', 'c']
    assert saida[0].similaridade == pytest.approx(esperado)
    assert saida[0].caracteristicas == ('genero:rock',)
    assert saida[1].similaridade == 0
    assert saida[1].motivo == 'sem_afinidade'
    assert saida[1].caracteristicas == ()


def test_pesos_tres_um_e_limite_por_gravacao():
    # Vetores ortogonais: perfil normalizado (3, 1) / sqrt(10).
    motor = Recomendador([Musica('a', 'A'), Musica('b', 'B'),
                          Musica('ca', 'A'), Musica('cb', 'B')])
    reviews = [r(1, 'a', 1), r(2, 'a'), r(3, 'b'), r(4, 'b', 3),
               r(5, 'ca'), r(6, 'cb')]
    likes = [Curtida(1, i) for i in (1, 2, 3, 4, 4)]
    saida = {s.musica: s for s in motor.recomendar(1, reviews, likes)}
    assert 'a' not in saida
    assert saida['ca'].similaridade == pytest.approx(3 / sqrt(10))
    assert saida['cb'].similaridade == pytest.approx(1 / sqrt(10))
    assert 'b' in saida  # curtir não exclui
    sem = motor.recomendar(1, reviews, [])
    assert next(s for s in sem if s.musica == 'cb').similaridade == 0


def test_representante_mais_curtida_nao_muda_score_e_descurtida():
    motor = Recomendador([Musica('a', 'A'), Musica('b', 'A')])
    reviews = [r(1, 'a', 1), r(2, 'b'), r(3, 'b', dias=1)]
    com = motor.recomendar(1, reviews, [Curtida(3, 2), Curtida(3, 2)])[0]
    sem = motor.recomendar(1, reviews, [])[0]
    assert (com.review_id, sem.review_id) == (2, 3)
    assert com.similaridade == sem.similaridade == pytest.approx(1)
    apagada = [replace(x, ativa=False) if x.id == 2 else x for x in reviews]
    assert motor.recomendar(1, apagada, [Curtida(3, 2)])[0].review_id == 3


def test_empate_representante_data_depois_id():
    motor = Recomendador([Musica('a', 'A')])
    assert motor.recomendar(1, [r(1, 'a'), r(2, 'a')], [])[0].review_id == 2


def test_fallback_intercala_artistas_e_preserva_recencia():
    motor = Recomendador([Musica('a', ' A '), Musica('b', 'a'), Musica('c', 'B'), Musica('d', 'B')])
    reviews = [r(1, 'a', dias=4), r(2, 'b', dias=3), r(3, 'c', dias=2), r(4, 'd', dias=1)]
    saida = motor.recomendar(1, reviews, [])
    assert chaves(saida) == ['a', 'c', 'b', 'd']
    assert {s.motivo for s in saida} == {'sem_sinais'}


def test_versoes_apagada_privacidade_isolamento():
    motor = Recomendador([Musica('original', 'A'), Musica('remix', 'A'), Musica('outra', 'B')])
    reviews = [r(1, 'original', 1), r(2, 'remix'), r(3, 'original'),
               r(4, 'outra', publica=False)]
    assert chaves(motor.recomendar(1, reviews, [])) == ['remix']
    apagadas = [replace(x, ativa=False) if x.id == 1 else x for x in reviews]
    saida = motor.recomendar(1, apagadas, [Curtida(1, 3), Curtida(1, 4)])
    assert set(chaves(saida)) == {'original', 'remix'}
    assert {s.motivo for s in saida} == {'afinidade'}
    assert {s.motivo for s in motor.recomendar(9, reviews, [Curtida(1, 2)])} == {'sem_sinais'}


def test_perfil_review_privada_propria_mas_nao_alheia():
    motor = Recomendador([Musica('a', 'A'), Musica('b', 'A')])
    reviews = [r(1, 'a', 1, publica=False), r(2, 'b')]
    assert motor.recomendar(1, reviews, [])[0].motivo == 'afinidade'
    assert motor.recomendar(3, reviews, [Curtida(3, 1)])[0].motivo == 'sem_sinais'


def test_normalizacao_termos_inteiros_campos_e_presenca_binaria():
    a = Musica('a', ' Banda  A ', (' ROCK ', 'rock'), ('ao vivo',))
    b = Musica('b', 'banda a', ('rock',), ('ao vivo',))
    c = Musica('c', 'rock')
    motor = Recomendador([a, b, c])
    saida = motor.recomendar(1, [r(1, 'a', 1), r(2, 'b'), r(3, 'c')], [])
    assert saida[0].similaridade == pytest.approx(1)
    assert set(saida[0].caracteristicas) == {'artista:banda a', 'genero:rock', 'tag:ao vivo'}
    assert saida[1].similaridade == 0


def test_ordem_independe_entrada_e_empate_chave():
    catalogo = [Musica(k, 'A') for k in ('a', 'b', 'c')]
    reviews = [r(1, 'a', 1), r(2, 'b'), r(3, 'c')]
    likes = [Curtida(4, 2), Curtida(5, 3)]
    esperado = Recomendador(catalogo).recomendar(1, reviews, likes)
    assert chaves(esperado) == ['b', 'c']
    for seed in range(10):
        rng = random.Random(seed)
        rng.shuffle(catalogo)
        rng.shuffle(reviews)
        rng.shuffle(likes)
        assert Recomendador(catalogo).recomendar(1, reviews, likes) == esperado


def test_vazios_e_vocabulario_vazio():
    assert Recomendador([]).recomendar(1, [], []) == ()
    motor = Recomendador([Musica('a', ''), Musica('b', '')])
    assert motor.recomendar(1, [r(1, 'a', 1), r(2, 'b')], [])[0].motivo == 'sem_sinais'
    assert motor.recomendar(1, [r(1, 'a', 1)], []) == ()


@pytest.mark.parametrize('reviews,likes', [
    ([r(1, 'inexistente')], []),
    ([r(1, 'a'), r(1, 'a', 3)], []),
    ([], [Curtida(1, 99)]),
    ([r(1, 'a')], [Curtida(True, 1)]),
    ([replace(r(1, 'a'), data=D.replace(tzinfo=None))], []),
    ([r(True, 'a')], []),
])
def test_entradas_invalidas(reviews, likes):
    with pytest.raises(EntradaInvalida):
        Recomendador([Musica('a', 'A')]).recomendar(1, reviews, likes)


def test_catalogo_e_usuario_invalidos():
    with pytest.raises(EntradaInvalida):
        Recomendador([Musica('a', 'A'), Musica('a', 'B')])
    with pytest.raises(EntradaInvalida):
        Recomendador([Musica('', 'A')])
    with pytest.raises(EntradaInvalida):
        Recomendador([]).recomendar(True, [], [])


def test_novo_indice_apos_mudanca_catalogo_preserva_anterior():
    catalogo = [Musica('a', 'A'), Musica('b', 'B')]
    reviews = [r(1, 'a', 1), r(2, 'b')]
    antigo = Recomendador(catalogo)
    novo = Recomendador([catalogo[0], replace(catalogo[1], artista='A')])
    assert antigo.recomendar(1, reviews, [])[0].similaridade == 0
    assert novo.recomendar(1, reviews, [])[0].similaridade == pytest.approx(1)
    with pytest.raises(EntradaInvalida):
        Recomendador([catalogo[0], catalogo[0]])
    assert antigo.recomendar(1, reviews, [])[0].similaridade == 0


def test_afinidade_nao_intercala_artistas_e_deduplica_reviews_identicas():
    motor = Recomendador([Musica(k, artista) for k, artista in
                          [('a', 'A'), ('b', 'A'), ('c', 'A'), ('d', 'B')]])
    reviews = [r(1, 'a', 1), r(2, 'b'), r(3, 'c'), r(4, 'd', dias=10)]
    saida = motor.recomendar(1, reviews + [reviews[1]], [])
    assert chaves(saida) == ['b', 'c', 'd']
