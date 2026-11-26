import pytest
from app.core.arvores import FlorestaReviews, NoInexistente, RegistroReview
from app.core.reputacao import (
    ErroReputacao, EventoCurtida, EventoDerivada, Reputacao, calcular_creditos,
)


@pytest.fixture
def arvore():
    f = FlorestaReviews()
    f.reconstruir([
        RegistroReview('a', 'm', 'ana'),
        RegistroReview('b', 'm', 'bia', 'a'),
        RegistroReview('c', 'm', 'caio', 'b'),
        RegistroReview('d', 'm', 'dani', 'c'),
        RegistroReview('ramo', 'm', 'eva', 'a'),
        RegistroReview('isolada', 'outra', 'ivo'),
        RegistroReview('repetida', 'm', 'bia', 'c'),
        RegistroReview('fim', 'm', 'leo', 'repetida'),
    ])
    return f


@pytest.mark.parametrize('evento,esperado', [
    (EventoCurtida('d', 'x'), {'dani': 4, 'caio': 2, 'bia': 1}),
    (EventoDerivada('d'), {'caio': 4, 'bia': 2, 'ana': 1}),
    (EventoCurtida('d', 'dani'), {'dani': 1}),
    (EventoCurtida('a', 'x'), {'ana': 4}),
    (EventoCurtida('isolada', 'x'), {'ivo': 4}),
    (EventoDerivada('ramo'), {'ana': 4}),
    (EventoCurtida('repetida', 'x'), {'bia': 4, 'caio': 2}),
    (EventoDerivada('fim'), {'bia': 4, 'caio': 2}),
])
def test_formula(arvore, evento, esperado):
    assert calcular_creditos(arvore, evento) == esperado


def test_idempotencia_reversao_recurtida(arvore):
    r = Reputacao()
    e = EventoCurtida('d', 'x')
    assert r.aplicar(arvore, e)
    assert not r.aplicar(arvore, e)
    assert r.total('dani') == 4
    assert r.remover(e)
    assert not r.remover(e)
    assert r.totais() == {}
    assert r.aplicar(arvore, e)
    assert r.total('dani') == 4


def test_acumula_e_separa_tipos(arvore):
    r = Reputacao()
    eventos = [EventoCurtida('d', 'x'), EventoCurtida('d', 'y'), EventoDerivada('d')]
    r.reconstruir(arvore, eventos)
    assert r.totais() == {'dani': 8, 'caio': 8, 'bia': 4, 'ana': 1}
    r.remover(eventos[0])
    assert r.contribuicoes(eventos[2]) == {'caio': 4, 'bia': 2, 'ana': 1}


def test_apagados_preservam_creditos_e_distancia(arvore):
    eventos = [EventoCurtida('d', 'x'), EventoDerivada('d')]
    r = Reputacao()
    r.reconstruir(arvore, eventos)
    antes = r.totais()
    for review in ('b', 'c', 'd'):
        arvore.marcar_apagada(review)
    r.reconstruir(arvore, eventos)
    assert r.totais() == antes


def test_reconstrucao_equivale_incremental(arvore):
    eventos = [EventoDerivada('d'), EventoCurtida('ramo', 'x'), EventoCurtida('d', 'x')]
    r = Reputacao()
    for e in eventos:
        r.aplicar(arvore, e)
    esperado = r.totais()
    for _ in range(2):
        r.reconstruir(arvore, reversed(eventos + eventos))
        assert r.totais() == esperado
    r.reconstruir(arvore, [])
    assert r.totais() == {}


@pytest.mark.parametrize('invalido,erro', [
    (EventoDerivada('a'), ErroReputacao),
    (EventoCurtida('ausente', 'x'), NoInexistente),
    (object(), ErroReputacao),
])
def test_erros_preservam_estado(arvore, invalido, erro):
    r = Reputacao()
    e = EventoCurtida('a', 'x')
    r.aplicar(arvore, e)
    antes = r.totais()
    with pytest.raises(erro):
        r.aplicar(arvore, invalido)
    assert r.totais() == antes
    with pytest.raises(erro):
        r.reconstruir(arvore, [EventoCurtida('d', 'x'), invalido])
    assert r.totais() == antes
    assert r.contribuicoes(e) == {'ana': 4}


def test_iteravel_falho_preserva_estado(arvore):
    def eventos():
        yield EventoDerivada('d')
        raise RuntimeError('fonte indisponível')
    r = Reputacao()
    r.aplicar(arvore, EventoCurtida('a', 'x'))
    with pytest.raises(RuntimeError):
        r.reconstruir(arvore, eventos())
    assert r.totais() == {'ana': 4}


def test_reversao_usa_creditos_originais(arvore):
    r = Reputacao()
    e = EventoCurtida('d', 'x')
    r.aplicar(arvore, e)
    arvore.reconstruir([RegistroReview('d', 'm', 'novo')])
    assert not r.aplicar(arvore, e)
    assert r.remover(e)
    assert r.totais() == {}
    r.aplicar(arvore, e)
    assert r.totais() == {'novo': 4}


def test_copias_nao_expoem_estado(arvore):
    r = Reputacao()
    e = EventoCurtida('a', 'x')
    assert r.contribuicoes(e) is None
    r.aplicar(arvore, e)
    r.contribuicoes(e).clear()
    r.totais().clear()
    assert r.total('ana') == 4
    assert r.total('ausente') == 0


@pytest.mark.parametrize('valor', [True, False, None, 1.2, [], {}])
def test_ids_invalidos(valor):
    with pytest.raises(ErroReputacao):
        EventoCurtida('a', valor)
    with pytest.raises(ErroReputacao):
        EventoCurtida(valor, 'x')
    with pytest.raises(ErroReputacao):
        EventoDerivada(valor)
    with pytest.raises(ErroReputacao):
        Reputacao().total(valor)


def test_ids_sem_coercao():
    f = FlorestaReviews()
    f.reconstruir([RegistroReview(1, 1, 1), RegistroReview('1', 1, '1')])
    r = Reputacao()
    r.reconstruir(f, [EventoCurtida(1, 'x'), EventoCurtida('1', 'x')])
    assert r.totais() == {1: 4, '1': 4}


def test_reconstrucao_usa_arvore_atual(arvore):
    r = Reputacao()
    e = EventoDerivada('d')
    r.aplicar(arvore, e)
    arvore.reconstruir([
        RegistroReview('nova-raiz', 'm', 'eva'),
        RegistroReview('d', 'm', 'dani', 'nova-raiz'),
    ])
    r.reconstruir(arvore, [e])
    assert r.totais() == {'eva': 4}
    assert r.contribuicoes(e) == {'eva': 4}


def test_registros_imutaveis():
    from dataclasses import FrozenInstanceError
    e = EventoCurtida('a', 'x')
    with pytest.raises(FrozenInstanceError):
        e.usuario_id = 'y'
