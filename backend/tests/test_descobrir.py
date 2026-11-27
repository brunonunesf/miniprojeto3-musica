"""Descobrir (#23): o recomendador do Bruno ligado à API, separado do feed.

Catálogo de teste (por chave): horizonte-original (Aurora do Vale, indie, guitarra, calma), horizonte-remaster (idêntica
à original em artista, gênero e tags), horizonte-vivo (Aurora, indie, acústico), horizonte-remix (Aurora, eletrônica,
dança), horizonte-outro-artista (Trio Ventania, forró, sanfona, dança) e mare-original (Lua de Barro, MPB).
"""

ORIGINAL = "demo-horizonte-original"
REMASTER = "demo-horizonte-remaster"
VIVO = "demo-horizonte-vivo"
REMIX = "demo-horizonte-remix"
FORRO = "demo-horizonte-outro-artista"
MPB = "demo-mare-original"


def review(client, quem, id_da_musica, chave, nota=8):
    r = client.post("/posts", json={"musica_id": id_da_musica(quem, chave), "nota": nota}, headers=quem)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def sugestoes(client, quem, **params):
    r = client.get("/descobrir", params=params, headers=quem)
    assert r.status_code == 200, r.text
    return r.json()


def chaves(pagina):
    return [i["review"]["musica"]["chave_catalogo"] for i in pagina["items"]]


def comunidade(client, logar, id_da_musica):
    """Bia avaliou quase todo o catálogo: é de onde saem as sugestões."""
    bia = logar("bia", "Bia")
    ids = {c: review(client, bia, id_da_musica, c) for c in (REMASTER, VIVO, REMIX, FORRO, MPB)}
    return bia, ids


# ---------- acesso e formato ----------


def test_exige_login(client):
    assert client.get("/descobrir").status_code == 401


def test_item_tem_a_review_no_formato_do_feed_e_a_explicacao(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")

    item = sugestoes(client, ana)["items"][0]

    assert set(item) == {"review", "explicacao"}
    assert {"id", "nota", "tem_texto", "curtidas", "curtido_por_mim", "comentarios", "autor", "musica"} <= set(item["review"])
    assert item["review"]["autor"]["username"] == "bia"
    assert isinstance(item["explicacao"], str) and item["explicacao"]


def test_a_resposta_nao_expoe_score_nem_perfil(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    review(client, ana, id_da_musica, ORIGINAL)

    texto = client.get("/descobrir", headers=ana).text

    for interno in ("similaridade", "caracteristicas", "motivo", "cosseno", "score", "perfil"):
        assert interno not in texto


# ---------- sem sinais (conta nova) ----------


def test_conta_sem_reviews_nem_curtidas_recebe_a_lista_de_recentes_nao_personalizada(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")

    pagina = sugestoes(client, ana)

    assert pagina["personalizada"] is False
    assert sorted(chaves(pagina)) == sorted([REMASTER, VIVO, REMIX, FORRO, MPB])  # uma review por música
    assert pagina["total"] == 5
    assert "ainda não avaliou nem curtiu" in pagina["items"][0]["explicacao"]


def test_sem_nenhuma_review_na_rede_a_lista_vem_vazia(client, logar):
    ana = logar("ana")

    pagina = sugestoes(client, ana)

    assert pagina["items"] == [] and pagina["total"] == 0 and pagina["personalizada"] is False


# ---------- personalização ----------


def test_a_afinidade_ordena_e_a_explicacao_diz_o_que_ha_em_comum(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    review(client, ana, id_da_musica, ORIGINAL)

    pagina = sugestoes(client, ana)

    assert pagina["personalizada"] is True
    # a remasterização tem tudo em comum com a original; depois a versão ao vivo (artista e gênero)
    assert chaves(pagina)[:2] == [REMASTER, VIVO]
    primeira = pagina["items"][0]["explicacao"]
    # até três termos em comum, os de maior contribuição (o gênero e as duas tags)
    assert "Em comum" in primeira and "gênero indie" in primeira and "tag guitarra" in primeira
    assert ORIGINAL not in chaves(pagina)  # o que já avaliou não volta


def test_sem_termos_em_comum_a_explicacao_diz_isso(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    review(client, ana, id_da_musica, ORIGINAL)

    pagina = sugestoes(client, ana)

    mpb = next(i for i in pagina["items"] if i["review"]["musica"]["chave_catalogo"] == MPB)
    assert "nada em comum" in mpb["explicacao"]
    # quem tem afinidade vem antes de quem não tem
    assert chaves(pagina).index(MPB) > chaves(pagina).index(REMIX)


def test_curtir_a_review_de_outra_pessoa_tambem_e_sinal(client, logar, id_da_musica):
    bia, ids = comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    assert sugestoes(client, ana)["personalizada"] is False

    client.post(f"/posts/{ids[REMASTER]}/curtir", headers=ana)

    pagina = sugestoes(client, ana)
    assert pagina["personalizada"] is True
    # curtir a review de outra pessoa não impede sugerir essa música (só a avaliação própria impede),
    # e o que tem a ver com o que ela curtiu vem primeiro: a própria remasterização, depois a ao vivo
    assert chaves(pagina)[:2] == [REMASTER, VIVO]


def test_descurtir_volta_a_conta_para_sem_sinais(client, logar, id_da_musica):
    bia, ids = comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    client.post(f"/posts/{ids[REMASTER]}/curtir", headers=ana)
    assert sugestoes(client, ana)["personalizada"] is True

    client.delete(f"/posts/{ids[REMASTER]}/curtir", headers=ana)

    assert sugestoes(client, ana)["personalizada"] is False


def test_curtir_a_propria_review_nao_e_sinal_alem_da_propria_review(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    minha = review(client, ana, id_da_musica, ORIGINAL)

    client.post(f"/posts/{minha}/curtir", headers=ana)
    com_curtida = chaves(sugestoes(client, ana))
    client.delete(f"/posts/{minha}/curtir", headers=ana)

    assert chaves(sugestoes(client, ana)) == com_curtida  # a auto-curtida não muda nada


def test_apagar_a_propria_review_devolve_a_musica_e_tira_o_sinal(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    minha = review(client, ana, id_da_musica, ORIGINAL)
    outra = logar("caio")
    review(client, outra, id_da_musica, ORIGINAL)  # outra pessoa também avaliou a original
    assert ORIGINAL not in chaves(sugestoes(client, ana))

    client.delete(f"/posts/{minha}", headers=ana)

    pagina = sugestoes(client, ana)
    assert ORIGINAL in chaves(pagina)  # volta a ser candidata, pela review do Caio
    assert pagina["personalizada"] is False  # e a conta ficou sem sinais


def test_review_apagada_de_outra_pessoa_nao_e_sugerida(client, logar, id_da_musica):
    bia, ids = comunidade(client, logar, id_da_musica)
    ana = logar("ana")

    client.delete(f"/posts/{ids[MPB]}", headers=bia)

    assert MPB not in chaves(sugestoes(client, ana))


# ---------- uma review por música ----------


def test_com_varias_reviews_da_mesma_musica_aparece_so_a_mais_curtida(client, logar, id_da_musica):
    bia, ids = comunidade(client, logar, id_da_musica)
    caio, leitor, ana = logar("caio"), logar("leitor"), logar("ana")
    do_caio = review(client, caio, id_da_musica, VIVO)
    client.post(f"/posts/{do_caio}/curtir", headers=leitor)  # a do Caio tem 1 curtida, a da Bia 0

    itens = [i for i in sugestoes(client, ana, limit=100)["items"] if i["review"]["musica"]["chave_catalogo"] == VIVO]

    assert [i["review"]["id"] for i in itens] == [do_caio]


# ---------- isolamento entre contas ----------


def test_cada_conta_recebe_o_ranking_do_proprio_gosto(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana, caio = logar("ana"), logar("caio")
    review(client, ana, id_da_musica, ORIGINAL)  # gosta de indie
    review(client, caio, id_da_musica, FORRO)  # gosta de forró e dança

    da_ana, do_caio = chaves(sugestoes(client, ana)), chaves(sugestoes(client, caio))

    assert da_ana[0] == REMASTER
    assert do_caio[0] == REMIX  # tem a tag "dança" em comum com o forró
    assert FORRO not in do_caio and ORIGINAL not in da_ana


def test_a_atividade_de_outra_conta_nao_muda_o_gosto_de_quem_pede(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    review(client, ana, id_da_musica, FORRO)
    antes = chaves(sugestoes(client, ana, limit=100))

    caio = logar("caio")  # outra pessoa avalia e curte à vontade, sem que Ana tenha feito nada
    review(client, caio, id_da_musica, ORIGINAL)
    client.post(f"/posts/{review(client, caio, id_da_musica, MPB)}/curtir", headers=caio)
    depois = chaves(sugestoes(client, ana, limit=100))

    # o perfil da Ana não mudou: o que ela recebe depois é o mesmo ranking, só com as músicas já existentes
    assert [c for c in depois if c in antes] == antes


# ---------- paginação e estabilidade ----------


def test_a_paginacao_e_depois_do_ranking_e_cobre_tudo_sem_repetir(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    review(client, ana, id_da_musica, ORIGINAL)
    completa = chaves(sugestoes(client, ana, limit=100))

    paginas = [sugestoes(client, ana, offset=o, limit=2) for o in (0, 2, 4)]

    assert [chaves(p) for p in paginas] == [completa[0:2], completa[2:4], completa[4:6]]
    assert all(p["total"] == len(completa) == 5 for p in paginas)
    assert all((p["offset"], p["limit"]) == (o, 2) for p, o in zip(paginas, (0, 2, 4)))


def test_depois_do_fim_a_pagina_vem_vazia_com_o_total(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")

    pagina = sugestoes(client, ana, offset=50)

    assert pagina["items"] == [] and pagina["total"] == 5


def test_mesmas_entradas_dao_a_mesma_resposta(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    review(client, ana, id_da_musica, ORIGINAL)

    assert client.get("/descobrir", headers=ana).json() == client.get("/descobrir", headers=ana).json()


def test_parametros_invalidos_dao_422(client, logar):
    ana = logar("ana")

    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": 2**70}):
        assert client.get("/descobrir", params=params, headers=ana).status_code == 422, params


# ---------- separado do feed ----------


def test_o_feed_continua_so_com_quem_a_pessoa_segue(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")

    assert client.get("/feed", headers=ana).json()["items"] == []  # não segue ninguém
    assert sugestoes(client, ana)["total"] == 5  # mas o Descobrir mostra a comunidade

    client.post("/usuarios/bia/follow", headers=ana)
    feed = client.get("/feed", headers=ana).json()
    assert feed["total"] == 5 and "explicacao" not in feed["items"][0]  # formato do feed intacto


def test_curtidas_e_comentarios_nas_sugestoes_sao_vistos_por_quem_pede(client, logar, id_da_musica):
    bia, ids = comunidade(client, logar, id_da_musica)
    ana, caio = logar("ana"), logar("caio")
    client.post(f"/posts/{ids[MPB]}/curtir", headers=ana)
    client.post(f"/posts/{ids[MPB]}/comentarios", json={"texto": "oi"}, headers=caio)

    da_ana = next(i for i in sugestoes(client, ana, limit=100)["items"] if i["review"]["id"] == ids[MPB])["review"]
    do_caio = next(i for i in sugestoes(client, caio, limit=100)["items"] if i["review"]["id"] == ids[MPB])["review"]

    assert (da_ana["curtidas"], da_ana["curtido_por_mim"], da_ana["comentarios"]) == (1, True, 1)
    assert (do_caio["curtidas"], do_caio["curtido_por_mim"]) == (1, False)


# ---------- revisão do #95: bordas ----------


def test_quem_ja_avaliou_todas_as_musicas_continua_personalizado_com_a_lista_vazia(client, logar, id_da_musica):
    ana = logar("ana")
    for chave in (ORIGINAL, REMASTER, VIVO, REMIX, FORRO, MPB):
        review(client, ana, id_da_musica, chave)

    pagina = sugestoes(client, ana)

    # a conta tem sinais de sobra: só não resta nada para sugerir
    assert pagina["items"] == [] and pagina["total"] == 0 and pagina["personalizada"] is True


def test_personalizada_vem_dos_sinais_da_conta_e_nao_do_ranking(client, logar, id_da_musica):
    bia, ids = comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    assert sugestoes(client, ana)["personalizada"] is False  # nada avaliado, nada curtido

    client.post(f"/posts/{ids[MPB]}/curtir", headers=ana)
    assert sugestoes(client, ana)["personalizada"] is True  # uma curtida basta

    client.delete(f"/posts/{ids[MPB]}/curtir", headers=ana)
    review(client, ana, id_da_musica, ORIGINAL)
    assert sugestoes(client, ana)["personalizada"] is True  # ou uma review própria


def test_se_o_recomendador_recusar_a_entrada_a_resposta_e_503_com_mensagem_simples(client, logar, monkeypatch):
    from app.core.recomendador import EntradaInvalida
    from app.services import descobrir as servico

    class Recusa:
        def recomendar(self, *args, **kwargs):
            raise EntradaInvalida("snapshot inconsistente")

    monkeypatch.setattr(servico, "_indice_do_catalogo", lambda musicas: (Recusa(), {}))
    ana = logar("ana")

    r = client.get("/descobrir", headers=ana)

    assert r.status_code == 503
    assert r.json() == {"detail": "não foi possível gerar sugestões agora"}  # sem expor o erro interno


def test_a_explicacao_usa_a_grafia_do_catalogo_e_nao_a_normalizada(client, logar, id_da_musica):
    comunidade(client, logar, id_da_musica)
    ana = logar("ana")
    review(client, ana, id_da_musica, ORIGINAL)

    vivo = next(i for i in sugestoes(client, ana)["items"] if i["review"]["musica"]["chave_catalogo"] == VIVO)

    # o recomendador compara "artista:aurora do vale"; quem lê vê "Aurora do Vale"
    assert "artista Aurora do Vale" in vivo["explicacao"]
    assert "aurora do vale" not in vivo["explicacao"]
