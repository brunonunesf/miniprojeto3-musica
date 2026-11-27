from dataclasses import FrozenInstanceError, replace
import pytest
from app.core.arvores import ErroArvore, FlorestaReviews, PlanoTrocaInvalido, RegistroReview


def floresta():
    f = FlorestaReviews()
    f.reconstruir([RegistroReview('a', 'm', 1), RegistroReview('j', 'm', 2, 'a'),
        RegistroReview('p', 'm', 3, 'j', True), RegistroReview('l', 'm', 4, 'p'),
        RegistroReview('irma', 'm', 5, 'a'), RegistroReview('b', 'm', 6),
        RegistroReview('c', 'm', 7, 'b'), RegistroReview('outra', 'x', 8)])
    return f


def snapshot(f):
    return (dict(f._nos), {k: list(v) for k, v in f._filhos.items()},
            {k: list(v) for k, v in f._raizes.items()}, f._revisao)


def test_movimento_repeticao_volta_e_reconstrucao():
    f = floresta()
    antes = snapshot(f)
    plano = f.preparar_troca_origem('j', 'c')
    assert snapshot(f) == antes
    assert plano.subarvore_ids == ('j', 'p', 'l')
    assert plano.caminho_anterior == ('a',)
    assert plano.caminho_novo == ('c', 'b')
    with pytest.raises(FrozenInstanceError):
        plano.alterou = False
    assert f.aplicar_troca_origem(plano) is plano
    assert f.raiz('l').review_id == 'b'
    assert f._filhos['a'] == ['irma']
    assert f._filhos['c'] == ['j']
    for id, registro in antes[0].items():
        assert f.consultar(id) == (replace(registro, origem_id='c') if id == 'j' else registro)
    reconstruida = FlorestaReviews()
    reconstruida.reconstruir(f._nos.values())
    assert snapshot(reconstruida)[:3] == snapshot(f)[:3]
    with pytest.raises(PlanoTrocaInvalido):
        f.aplicar_troca_origem(plano)
    repetido = f.preparar_troca_origem('j', 'c')
    assert not repetido.alterou and repetido.subarvore_ids == ()
    assert repetido.caminho_anterior == repetido.caminho_novo
    estado = snapshot(f)
    f.aplicar_troca_origem(repetido)
    assert snapshot(f) == estado
    f.aplicar_troca_origem(f.preparar_troca_origem('j', 'a'))
    assert f.raiz('l').review_id == 'a'


@pytest.mark.parametrize('review,destino', [('j','j'), ('j','p'), ('j','l'),
    ('j','outra'), ('j','ausente'), ('ausente','a'), ('a','b'), ('p','b'),
    ('j',None), ('j',True), (True,'a')])
def test_rejeicao_preserva_estado(review, destino):
    f = floresta()
    antes = snapshot(f)
    with pytest.raises(ErroArvore):
        f.preparar_troca_origem(review, destino)
    assert snapshot(f) == antes


def test_origem_apagada_e_ordem_entre_ramos():
    f = floresta()
    f.marcar_apagada('a')
    f.aplicar_troca_origem(f.preparar_troca_origem('j', 'irma'))
    assert f._filhos['a'] == ['irma']
    assert f._filhos['irma'] == ['j']
    with pytest.raises(ErroArvore):
        f.preparar_troca_origem('j', 'a')
    f.inserir(RegistroReview('novo', 'm', 9, 'b'))
    f.aplicar_troca_origem(f.preparar_troca_origem('j', 'b'))
    assert f._filhos['b'] == ['c', 'novo', 'j']
    assert f._filhos['j'] == ['p']


@pytest.mark.parametrize('mutacao', ['inserir','apagar','reconstruir','trocar'])
def test_mutacao_invalida_plano(mutacao):
    f = floresta()
    plano = f.preparar_troca_origem('j', 'b')
    if mutacao == 'inserir':
        f.inserir(RegistroReview('novo', 'm', 10))
    elif mutacao == 'apagar':
        f.marcar_apagada('irma')
    elif mutacao == 'reconstruir':
        f.reconstruir(list(f._nos.values()))
    else:
        f.aplicar_troca_origem(f.preparar_troca_origem('c', 'a'))
    antes = snapshot(f)
    with pytest.raises(PlanoTrocaInvalido):
        f.aplicar_troca_origem(plano)
    assert snapshot(f) == antes


def test_plano_estrangeiro_copiado_e_malformado():
    f = floresta()
    plano = f.preparar_troca_origem('j', 'b')
    for invalido in [plano, replace(plano), None, {}]:
        alvo = floresta() if invalido is plano else f
        antes = snapshot(alvo)
        with pytest.raises(PlanoTrocaInvalido):
            alvo.aplicar_troca_origem(invalido)
        assert snapshot(alvo) == antes


def test_falhas_e_noops_nao_invalidam_plano():
    f = floresta()
    plano = f.preparar_troca_origem('j', 'b')
    f.marcar_apagada('p')
    f.aplicar_troca_origem(f.preparar_troca_origem('c', 'b'))
    with pytest.raises(ErroArvore):
        f.reconstruir([RegistroReview('x', 'm', 1, 'ausente')])
    with pytest.raises(ErroArvore):
        f.inserir(f.consultar('a'))
    f.aplicar_troca_origem(plano)
    assert f.pai('j').review_id == 'b'


def test_corrente_longa():
    f = FlorestaReviews()
    f.reconstruir([RegistroReview(i, 'm', i, i-1 if i else None,
                                  apagada=(i == 150)) for i in range(1100)]
                 + [RegistroReview('destino', 'm', 2000)])
    antes = snapshot(f)
    with pytest.raises(ErroArvore):
        f.preparar_troca_origem(1, 1099)
    assert snapshot(f) == antes
    plano = f.preparar_troca_origem(1, 'destino')
    assert plano.subarvore_ids == tuple(range(1, 1100))
    f.aplicar_troca_origem(plano)
    assert f.raiz(1099).review_id == 'destino'
    assert len(f.preparar_troca_origem(1099, 0).caminho_anterior) == 1099


def test_bfs_com_ramificacao_e_plano_noop_obsoleto():
    f = floresta()
    f.inserir(RegistroReview('ramo', 'm', 9, 'j'))
    f.inserir(RegistroReview('folha', 'm', 10, 'ramo'))
    noop = f.preparar_troca_origem('j', 'a')
    plano = f.preparar_troca_origem('j', 'b')
    assert plano.subarvore_ids == ('j', 'p', 'ramo', 'l', 'folha')
    f.aplicar_troca_origem(plano)
    assert tuple(p.no.review_id for p in f.descendentes('j').itens) == plano.subarvore_ids[1:]
    with pytest.raises(PlanoTrocaInvalido):
        f.aplicar_troca_origem(noop)
