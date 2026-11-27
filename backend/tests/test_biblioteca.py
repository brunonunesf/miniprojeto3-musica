"""Bibliotecas e privacidade (issue #12).

Cada pessoa tem duas listas calculadas das reviews dela: descobertas (reviews derivadas) e recomendações (reviews
independentes). Padrão: descobertas privadas, recomendações públicas; só a dona muda isso.
"""

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models.visibilidade_biblioteca import VisibilidadeBiblioteca

MARE = "demo-mare-original"
HORIZONTE = "demo-horizonte-original"
REMIX = "demo-horizonte-remix"
VIVO = "demo-horizonte-vivo"


def criar(client, quem, id_da_musica, chave, texto="", origem_id=None):
    corpo = {"musica_id": id_da_musica(quem, chave), "nota": 8, "texto": texto}
    if origem_id is not None:
        corpo["origem_id"] = origem_id
    r = client.post("/posts", json=corpo, headers=quem)
    assert r.status_code == 201, r.text
    return r.json()


def resumo(client, quem, username):
    r = client.get(f"/usuarios/{username}/biblioteca", headers=quem)
    assert r.status_code == 200, r.text
    return r.json()


def lista(client, quem, username, nome, **params):
    return client.get(f"/usuarios/{username}/biblioteca/{nome}", params=params, headers=quem)


def definir(client, quem, **corpo):
    return client.patch("/usuarios/eu/biblioteca", json=corpo, headers=quem)


def musicas_da(pagina):
    return [i["musica"]["chave_catalogo"] for i in pagina["items"]]


def cenario(client, logar, id_da_musica):
    """Ana indica MARE e HORIZONTE (recomendações). Júlia descobre MARE pela Ana e indica VIVO por conta própria."""
    ana, julia, leitor = logar("ana"), logar("julia"), logar("leitor")
    a_mare = criar(client, ana, id_da_musica, MARE, "indico")
    criar(client, ana, id_da_musica, HORIZONTE, "indico também")
    j_mare = criar(client, julia, id_da_musica, MARE, "pela Ana", origem_id=a_mare["id"])
    criar(client, julia, id_da_musica, VIVO, "minha")
    return ana, julia, leitor, {"a_mare": a_mare, "j_mare": j_mare}


# ---------- o que entra em cada lista ----------


def test_padrao_descobertas_privadas_e_recomendacoes_publicas(client, logar):
    ana, leitor = logar("ana"), logar("leitor")

    para_ela = resumo(client, ana, "ana")
    para_outro = resumo(client, leitor, "ana")

    assert para_ela["descobertas"] == {"visibilidade": "privada", "acessivel": True, "total": 0}
    assert para_ela["recomendacoes"] == {"visibilidade": "publica", "acessivel": True, "total": 0}
    assert para_outro["descobertas"] == {"visibilidade": "privada", "acessivel": False, "total": None}
    assert para_outro["recomendacoes"] == {"visibilidade": "publica", "acessivel": True, "total": 0}


def test_derivada_vira_descoberta_e_independente_vira_recomendacao(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)

    descobertas = lista(client, julia, "julia", "descobertas").json()
    recomendacoes = lista(client, julia, "julia", "recomendacoes").json()

    assert musicas_da(descobertas) == [MARE] and descobertas["total"] == 1
    assert musicas_da(recomendacoes) == [VIVO] and recomendacoes["total"] == 1
    # a descoberta traz de onde veio
    item = descobertas["items"][0]
    assert item["origem_id"] == r["a_mare"]["id"] and item["origem"]["autor"]["username"] == "ana"
    # e o resumo concorda com as listas
    assert resumo(client, julia, "julia")["descobertas"]["total"] == 1
    assert resumo(client, julia, "julia")["recomendacoes"]["total"] == 1


def test_o_item_e_a_review_no_formato_do_feed(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)

    item = lista(client, julia, "julia", "descobertas").json()["items"][0]

    assert {"id", "nota", "tem_texto", "curtidas", "curtido_por_mim", "comentarios", "autor", "musica", "origem"} <= set(item)
    assert item["musica"]["titulo"] and item["musica"]["artista"] and "tipo_versao" in item["musica"]


def test_uma_musica_aparece_uma_vez_e_o_mais_novo_vem_primeiro(client, logar, id_da_musica):
    ana = logar("ana")
    criar(client, ana, id_da_musica, MARE, "primeira")
    criar(client, ana, id_da_musica, HORIZONTE, "segunda")
    criar(client, ana, id_da_musica, VIVO, "terceira")

    pagina = lista(client, ana, "ana", "recomendacoes").json()

    assert musicas_da(pagina) == [VIVO, HORIZONTE, MARE] and len(set(musicas_da(pagina))) == 3


def test_curtir_comentar_e_visitar_nao_registram_nada(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)

    client.post(f"/posts/{r['a_mare']['id']}/curtir", headers=leitor)
    client.post(f"/posts/{r['a_mare']['id']}/comentarios", json={"texto": "oi"}, headers=leitor)
    client.get(f"/posts/{r['a_mare']['id']}", headers=leitor)

    resumo_do_leitor = resumo(client, leitor, "leitor")
    assert resumo_do_leitor["descobertas"]["total"] == 0 and resumo_do_leitor["recomendacoes"]["total"] == 0


def test_pessoa_sem_musicas_tem_listas_vazias_e_acessiveis_para_ela(client, logar):
    ana = logar("ana")

    for nome in ("descobertas", "recomendacoes"):
        pagina = lista(client, ana, "ana", nome).json()
        assert pagina["items"] == [] and pagina["total"] == 0


# ---------- privacidade ----------


def test_terceiro_ve_a_lista_publica_e_e_negado_na_privada_sem_vazar_nada(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)

    publica = lista(client, leitor, "julia", "recomendacoes")
    privada = lista(client, leitor, "julia", "descobertas")

    assert publica.status_code == 200 and musicas_da(publica.json()) == [VIVO]
    assert privada.status_code == 403
    assert set(privada.json()) == {"detail"}  # nenhum item, contagem ou origem na negativa
    assert MARE not in privada.text and "ana" not in privada.text
    assert resumo(client, leitor, "julia")["descobertas"] == {"visibilidade": "privada", "acessivel": False, "total": None}


def test_lista_privada_vazia_tambem_e_negada_para_nao_revelar_que_esta_vazia(client, logar):
    ana, leitor = logar("ana"), logar("leitor")

    assert lista(client, leitor, "ana", "descobertas").status_code == 403  # vazia, mas privada


def test_as_quatro_combinacoes_de_visibilidade(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)
    esperado = {  # (descobertas, recomendacoes) -> o que um terceiro consegue abrir
        ("privada", "publica"): (403, 200),
        ("publica", "publica"): (200, 200),
        ("privada", "privada"): (403, 403),
        ("publica", "privada"): (200, 403),
    }

    for (d, rec), (codigo_d, codigo_r) in esperado.items():
        assert definir(client, julia, descobertas=d, recomendacoes=rec).status_code == 200
        assert lista(client, leitor, "julia", "descobertas").status_code == codigo_d, (d, rec)
        assert lista(client, leitor, "julia", "recomendacoes").status_code == codigo_r, (d, rec)
        # a dona abre as duas em qualquer combinação
        assert lista(client, julia, "julia", "descobertas").status_code == 200
        assert lista(client, julia, "julia", "recomendacoes").status_code == 200


def test_as_reviews_continuam_publicas_no_perfil_mesmo_com_a_lista_privada(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)
    definir(client, julia, descobertas="privada", recomendacoes="privada")

    do_perfil = client.get("/usuarios/julia/posts", headers=leitor).json()

    assert sorted(i["musica"]["chave_catalogo"] for i in do_perfil["items"]) == sorted([MARE, VIVO])


def test_a_visibilidade_de_uma_pessoa_nao_afeta_a_de_outra(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)

    definir(client, julia, descobertas="publica")

    assert lista(client, leitor, "julia", "descobertas").status_code == 200
    assert lista(client, leitor, "ana", "descobertas").status_code == 403  # a da Ana segue no padrão


# ---------- mudar a visibilidade ----------


def test_mudar_uma_lista_nao_mexe_na_outra_e_repetir_nao_muda_nada(client, logar):
    ana = logar("ana")

    primeira = definir(client, ana, descobertas="publica").json()
    repetida = definir(client, ana, descobertas="publica").json()

    assert primeira == repetida
    assert primeira["descobertas"]["visibilidade"] == "publica"
    assert primeira["recomendacoes"]["visibilidade"] == "publica"  # continua no padrão
    assert definir(client, ana, recomendacoes="privada").json()["descobertas"]["visibilidade"] == "publica"  # a outra ficou


def test_so_a_propria_pessoa_muda_e_exige_login_e_valores_validos(client, logar):
    ana = logar("ana")

    assert client.patch("/usuarios/eu/biblioteca", json={"descobertas": "publica"}).status_code == 401
    for corpo in ({}, {"descobertas": "talvez"}, {"recomendacoes": 1}, {"descobertas": None, "recomendacoes": None}):
        assert definir(client, ana, **corpo).status_code == 422, corpo


def test_a_linha_so_existe_depois_da_primeira_mudanca(client, logar):
    ana = logar("ana")
    resumo(client, ana, "ana")
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(VisibilidadeBiblioteca)) == 0

    definir(client, ana, descobertas="publica")

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(VisibilidadeBiblioteca)) == 1


def test_primeira_mudanca_simultanea_da_mesma_pessoa_nao_da_500(client, logar):
    ana = logar("ana")

    with ThreadPoolExecutor(max_workers=6) as pool:
        codigos = list(pool.map(lambda v: definir(client, ana, descobertas=v).status_code, ["publica", "privada"] * 3))

    assert set(codigos) <= {200, 409} and 200 in codigos
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(VisibilidadeBiblioteca)) == 1  # uma linha só


# ---------- coerência com exclusão e correção de origem ----------


def test_apagar_a_review_a_tira_da_lista(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)

    client.delete(f"/posts/{r['j_mare']['id']}", headers=julia)

    assert lista(client, julia, "julia", "descobertas").json()["items"] == []
    assert resumo(client, julia, "julia")["descobertas"]["total"] == 0


def test_apagar_a_origem_mantem_a_descoberta_sem_dizer_de_quem_veio(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)

    client.delete(f"/posts/{r['a_mare']['id']}", headers=ana)  # a origem da Júlia some

    item = lista(client, julia, "julia", "descobertas").json()["items"][0]
    assert item["musica"]["chave_catalogo"] == MARE
    assert item["origem_id"] == r["a_mare"]["id"] and item["origem"] is None  # a referência fica, sem conteúdo


def test_corrigir_a_origem_atualiza_de_onde_a_descoberta_veio(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)
    caio = logar("caio")
    do_caio = criar(client, caio, id_da_musica, MARE, "indico também")

    assert client.patch(f"/posts/{r['j_mare']['id']}/origem", json={"origem_id": do_caio["id"]}, headers=julia).status_code == 200

    item = lista(client, julia, "julia", "descobertas").json()["items"][0]
    assert item["origem_id"] == do_caio["id"] and item["origem"]["autor"]["username"] == "caio"
    assert resumo(client, julia, "julia")["descobertas"]["total"] == 1  # continua uma só, sem duplicar


def test_publicar_uma_derivada_depois_aumenta_as_descobertas(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)
    do_ana = criar(client, ana, id_da_musica, REMIX, "remix")

    criar(client, julia, id_da_musica, REMIX, "pela Ana", origem_id=do_ana["id"])

    assert sorted(musicas_da(lista(client, julia, "julia", "descobertas").json())) == sorted([MARE, REMIX])


# ---------- lista, usuário e paginação ----------


def test_lista_ou_usuario_inexistente_da_404_inclusive_link_antigo(client, logar):
    ana = logar("ana")

    for url in ("/usuarios/ana/biblioteca/favoritas", "/usuarios/ana/biblioteca/escutas", "/usuarios/ninguem/biblioteca",
                "/usuarios/ninguem/biblioteca/descobertas"):
        assert client.get(url, headers=ana).status_code == 404, url


def test_exige_login(client, logar):
    logar("ana")

    assert client.get("/usuarios/ana/biblioteca").status_code == 401
    assert client.get("/usuarios/ana/biblioteca/recomendacoes").status_code == 401


def test_paginacao_cobre_tudo_sem_repetir_e_valida_os_limites(client, logar, id_da_musica):
    ana = logar("ana")
    for chave in (MARE, HORIZONTE, VIVO, REMIX):
        criar(client, ana, id_da_musica, chave)
    completa = musicas_da(lista(client, ana, "ana", "recomendacoes", limit=100).json())

    paginas = [lista(client, ana, "ana", "recomendacoes", offset=o, limit=3).json() for o in (0, 3)]

    assert [musicas_da(p) for p in paginas] == [completa[:3], completa[3:]]
    assert all(p["total"] == 4 and p["lista"] == "recomendacoes" and p["visibilidade"] == "publica" for p in paginas)
    assert lista(client, ana, "ana", "recomendacoes", offset=50).json()["items"] == []  # depois do fim
    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": 2**70}):
        assert lista(client, ana, "ana", "recomendacoes", **params).status_code == 422, params


def test_a_pagina_traz_curtidas_e_comentarios_vistos_por_quem_pede(client, logar, id_da_musica):
    ana, julia, leitor, r = cenario(client, logar, id_da_musica)
    client.post(f"/posts/{r['a_mare']['id']}/curtir", headers=leitor)

    vista_pelo_leitor = lista(client, leitor, "ana", "recomendacoes").json()["items"]
    do_mare = next(i for i in vista_pelo_leitor if i["id"] == r["a_mare"]["id"])

    assert do_mare["curtidas"] == 1 and do_mare["curtido_por_mim"] is True
