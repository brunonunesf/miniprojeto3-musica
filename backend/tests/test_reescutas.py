"""Reescutas: o aviso "ouvi novamente" (issue #12).

Um aviso não é review: não cria nó, música nem pontos. Só o autor da review avisa, com comentário opcional, e no máximo uma
vez por pessoa e música a cada 24 horas (janela móvel, contada do aviso mais recente), mesmo com requisições simultâneas.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models.evento_reputacao import EventoReputacao
from app.models.post import Post
from app.models.reescuta import Reescuta

MARE = "demo-mare-original"
HORIZONTE = "demo-horizonte-original"
INICIO = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)


class Relogio:
    def __init__(self):
        self.agora = INICIO

    def avancar(self, **tempo):
        self.agora += timedelta(**tempo)


@pytest.fixture()
def relogio(monkeypatch):
    """O relógio do servidor, parado no INICIO e movido à mão: testa 'antes' e 'exatamente depois' de 24 horas."""
    from app.services import reescutas

    r = Relogio()
    monkeypatch.setattr(reescutas, "agora", lambda: r.agora)
    return r


def criar(client, quem, id_da_musica, chave=MARE, texto="", origem_id=None):
    corpo = {"musica_id": id_da_musica(quem, chave), "nota": 8, "texto": texto}
    if origem_id is not None:
        corpo["origem_id"] = origem_id
    r = client.post("/posts", json=corpo, headers=quem)
    assert r.status_code == 201, r.text
    return r.json()


def avisar(client, quem, post_id, comentario=None):
    corpo = {} if comentario is None else {"comentario": comentario}
    return client.post(f"/posts/{post_id}/reescutas", json=corpo, headers=quem)


def da_review(client, quem, post_id, **params):
    r = client.get(f"/posts/{post_id}/reescutas", params=params, headers=quem)
    assert r.status_code == 200, r.text
    return r.json()


def pontos(client, leitor, *usernames):
    return {u: client.get(f"/usuarios/{u}", headers=leitor).json()["reputacao"] for u in usernames}


def contagens():
    with SessionLocal() as db:
        return {
            "reviews": db.scalar(select(func.count()).select_from(Post)),
            "eventos": db.scalar(select(func.count()).select_from(EventoReputacao)),
            "avisos": db.scalar(select(func.count()).select_from(Reescuta)),
        }


# ---------- registrar ----------


def test_o_autor_registra_com_comentario_e_a_resposta_traz_a_review_atual(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica, texto="adoro")

    resposta = avisar(client, ana, r["id"], "voltei a ouvir no ônibus")

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["comentario"] == "voltei a ouvir no ônibus"
    assert corpo["created_at"].startswith("2026-11-27T12:00:00")
    assert corpo["review"]["id"] == r["id"] and corpo["review"]["autor"]["username"] == "ana"
    assert {"nota", "musica", "curtidas", "curtido_por_mim", "comentarios"} <= set(corpo["review"])


def test_o_comentario_e_opcional_e_so_espacos_vale_como_vazio(client, logar, id_da_musica, relogio):
    ana, bia = logar("ana"), logar("bia")
    a, b = criar(client, ana, id_da_musica), criar(client, bia, id_da_musica)

    assert avisar(client, ana, a["id"]).json()["comentario"] == ""  # sem corpo
    assert avisar(client, bia, b["id"], "   ").json()["comentario"] == ""  # só espaços


def test_comentario_longo_demais_e_recusado_sem_gravar(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)

    assert avisar(client, ana, r["id"], "x" * 501).status_code == 422
    assert avisar(client, ana, r["id"], "x" * 500).status_code == 201  # no limite, passa (e o recusado não gastou a janela)


def test_review_alheia_inexistente_e_sem_login(client, logar, id_da_musica, relogio):
    ana, bia = logar("ana"), logar("bia")
    r = criar(client, ana, id_da_musica)

    assert avisar(client, bia, r["id"]).status_code == 403  # a review é da Ana
    assert avisar(client, ana, 9999).status_code == 404
    assert client.post(f"/posts/{r['id']}/reescutas", json={}).status_code == 401
    assert avisar(client, ana, 2**70).status_code == 422
    assert da_review(client, ana, r["id"])["total"] == 0  # nenhuma das tentativas gravou nada


def test_quem_segue_tambem_nao_avisa_pela_review_de_outra_pessoa(client, logar, id_da_musica, relogio):
    ana, bia = logar("ana"), logar("bia")
    r = criar(client, ana, id_da_musica)
    client.post("/usuarios/ana/follow", headers=bia)

    assert avisar(client, bia, r["id"]).status_code == 403


# ---------- o limite de 24 horas ----------


def test_um_aviso_por_musica_a_cada_24_horas_e_a_borda_e_exata(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)
    assert avisar(client, ana, r["id"], "primeiro").status_code == 201

    relogio.avancar(hours=23, minutes=59, seconds=59)  # um segundo antes
    bloqueado = avisar(client, ana, r["id"], "cedo demais")
    assert bloqueado.status_code == 429 and bloqueado.headers["Retry-After"] == "1"

    relogio.avancar(seconds=1)  # exatamente 24 horas depois do primeiro
    assert avisar(client, ana, r["id"], "liberou").status_code == 201
    assert da_review(client, ana, r["id"])["total"] == 2


def test_a_resposta_de_bloqueio_diz_quando_tentar_de_novo(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)
    avisar(client, ana, r["id"])

    relogio.avancar(hours=11, minutes=30)
    bloqueado = avisar(client, ana, r["id"])

    assert bloqueado.status_code == 429
    assert bloqueado.headers["Retry-After"] == str(12 * 3600 + 30 * 60)  # faltam 12 h e 30 min
    assert "12 h e 30 min" in bloqueado.json()["detail"]


def test_a_janela_e_movel_e_conta_do_aviso_mais_recente(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)
    avisar(client, ana, r["id"])  # t = 0
    relogio.avancar(hours=24)
    assert avisar(client, ana, r["id"]).status_code == 201  # t = 24 h

    relogio.avancar(hours=23)  # t = 47 h: só 23 h depois do segundo, mesmo com 47 h do primeiro
    assert avisar(client, ana, r["id"]).status_code == 429
    relogio.avancar(hours=1)  # t = 48 h
    assert avisar(client, ana, r["id"]).status_code == 201


def test_o_limite_e_por_pessoa_e_por_musica(client, logar, id_da_musica, relogio):
    ana, bia = logar("ana"), logar("bia")
    a_mare, a_horizonte, b_mare = (
        criar(client, ana, id_da_musica, MARE),
        criar(client, ana, id_da_musica, HORIZONTE),
        criar(client, bia, id_da_musica, MARE),
    )
    assert avisar(client, ana, a_mare["id"]).status_code == 201

    assert avisar(client, ana, a_horizonte["id"]).status_code == 201  # outra música da mesma pessoa
    assert avisar(client, bia, b_mare["id"]).status_code == 201  # a mesma música, outra pessoa
    assert avisar(client, ana, a_mare["id"]).status_code == 429  # a mesma pessoa e música


def test_o_aviso_recusado_nao_gasta_a_janela_nem_grava(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)
    avisar(client, ana, r["id"], "valido")

    for _ in range(3):
        assert avisar(client, ana, r["id"], "repetido").status_code == 429

    assert da_review(client, ana, r["id"])["total"] == 1
    relogio.avancar(hours=24)  # a janela segue contando só do aviso que valeu
    assert avisar(client, ana, r["id"]).status_code == 201


def test_com_requisicoes_simultaneas_so_uma_passa(client, logar, id_da_musica):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)

    with ThreadPoolExecutor(max_workers=8) as pool:
        codigos = list(pool.map(lambda i: avisar(client, ana, r["id"], f"aviso {i}").status_code, range(16)))

    assert codigos.count(201) == 1 and set(codigos) <= {201, 429}  # nunca 500
    assert contagens()["avisos"] == 1


# ---------- o que um aviso não é ----------


def test_nao_cria_review_no_nem_pontos_e_nao_muda_o_ranking(client, logar, id_da_musica, relogio):
    ana, julia, pedro, leitor = logar("ana"), logar("julia"), logar("pedro"), logar("leitor")
    a = criar(client, ana, id_da_musica, texto="indico")
    j = criar(client, julia, id_da_musica, texto="pela Ana", origem_id=a["id"])
    p = criar(client, pedro, id_da_musica, texto="pela Júlia", origem_id=j["id"])
    client.post(f"/posts/{p['id']}/curtir", headers=leitor)
    antes = {
        "pontos": pontos(client, leitor, "ana", "julia", "pedro"),
        "contagens": contagens(),
        "arvore": client.get(f"/posts/{a['id']}/arvore", headers=leitor).json(),
        "populares": client.get("/musicas/populares", headers=leitor).json(),
        "feed_ana": client.get("/feed", headers=leitor).json(),
    }

    for dono, review in ((ana, a), (julia, j), (pedro, p)):  # inclusive nas derivadas, no meio da corrente
        assert avisar(client, dono, review["id"], "de novo").status_code == 201

    assert pontos(client, leitor, "ana", "julia", "pedro") == antes["pontos"]
    depois = contagens()
    assert (depois["reviews"], depois["eventos"]) == (antes["contagens"]["reviews"], antes["contagens"]["eventos"])
    assert depois["avisos"] == 3
    assert client.get(f"/posts/{a['id']}/arvore", headers=leitor).json() == antes["arvore"]
    assert client.get("/musicas/populares", headers=leitor).json() == antes["populares"]  # reescuta não conta como review
    assert client.get("/feed", headers=leitor).json() == antes["feed_ana"]  # o contrato do feed não mudou


def test_a_curtida_continua_unica_e_e_na_review_original(client, logar, id_da_musica, relogio):
    ana, leitor = logar("ana"), logar("leitor")
    r = criar(client, ana, id_da_musica)
    avisar(client, ana, r["id"])
    avisar_de_novo = (relogio.avancar(hours=24), avisar(client, ana, r["id"]))[1]
    assert avisar_de_novo.status_code == 201

    for _ in range(3):
        client.post(f"/posts/{r['id']}/curtir", headers=leitor)

    assert client.get(f"/posts/{r['id']}", headers=leitor).json()["curtidas"] == 1  # duas reescutas, uma curtida
    avisos = da_review(client, leitor, r["id"])["items"]
    assert [a["review"]["id"] for a in avisos] == [r["id"], r["id"]]  # as ações apontam para a review original
    assert all(a["review"]["curtidas"] == 1 and a["review"]["curtido_por_mim"] is True for a in avisos)


# ---------- edição e exclusão ----------


def test_editar_a_review_depois_nao_muda_a_data_nem_o_comentario_do_aviso(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica, texto="primeira impressão")
    avisar(client, ana, r["id"], "de novo!")
    relogio.avancar(hours=5)

    assert client.patch(f"/posts/{r['id']}", json={"nota": 3, "texto": "mudei de ideia"}, headers=ana).status_code == 200

    aviso = da_review(client, ana, r["id"])["items"][0]
    assert aviso["comentario"] == "de novo!" and aviso["created_at"].startswith("2026-11-27T12:00:00")  # os do aviso
    assert aviso["review"]["nota"] == 3  # e a review é a de agora
    assert avisar(client, ana, r["id"]).status_code == 429  # editar também não reabre a janela


def test_apagar_a_review_apaga_os_avisos(client, logar, id_da_musica, relogio):
    ana, leitor = logar("ana"), logar("leitor")
    r = criar(client, ana, id_da_musica)
    client.post("/usuarios/ana/follow", headers=leitor)
    avisar(client, ana, r["id"], "sumiu junto")
    assert client.get("/feed/reescutas", headers=leitor).json()["total"] == 1

    assert client.delete(f"/posts/{r['id']}", headers=ana).status_code == 204

    assert client.get("/feed/reescutas", headers=leitor).json()["total"] == 0
    assert contagens()["avisos"] == 0
    assert client.get(f"/posts/{r['id']}/reescutas", headers=ana).status_code == 404


# ---------- leitura ----------


def test_os_avisos_da_review_vem_do_mais_novo_ao_mais_antigo_e_paginados(client, logar, id_da_musica, relogio):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)
    for i in range(3):
        avisar(client, ana, r["id"], f"vez {i}")
        relogio.avancar(hours=24)

    tudo = da_review(client, ana, r["id"], limit=100)
    paginas = [da_review(client, ana, r["id"], offset=o, limit=2) for o in (0, 2)]

    assert [a["comentario"] for a in tudo["items"]] == ["vez 2", "vez 1", "vez 0"] and tudo["total"] == 3
    assert [[a["comentario"] for a in p["items"]] for p in paginas] == [["vez 2", "vez 1"], ["vez 0"]]
    assert all(p["total"] == 3 for p in paginas)
    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": 2**70}):
        assert client.get(f"/posts/{r['id']}/reescutas", params=params, headers=ana).status_code == 422, params


def test_os_avisos_do_feed_sao_so_de_quem_se_segue_em_ordem_cronologica(client, logar, id_da_musica, relogio):
    ana, bia, caio, leitor = logar("ana"), logar("bia"), logar("caio"), logar("leitor")
    a, b, c, l = (criar(client, quem, id_da_musica) for quem in (ana, bia, caio, leitor))
    for seguido in ("ana", "bia"):  # o leitor segue Ana e Bia, não o Caio
        client.post(f"/usuarios/{seguido}/follow", headers=leitor)
    avisar(client, ana, a["id"], "da Ana")
    relogio.avancar(minutes=10)
    avisar(client, caio, c["id"], "do Caio (não seguido)")
    avisar(client, leitor, l["id"], "meu")
    relogio.avancar(minutes=10)
    avisar(client, bia, b["id"], "da Bia")

    pagina = client.get("/feed/reescutas", headers=leitor).json()

    assert [x["comentario"] for x in pagina["items"]] == ["da Bia", "da Ana"]  # mais novo primeiro, sem Caio nem o próprio
    assert pagina["total"] == 2 and all("review" in x for x in pagina["items"])


def test_o_feed_de_reviews_nao_ganha_avisos(client, logar, id_da_musica, relogio):
    ana, leitor = logar("ana"), logar("leitor")
    r = criar(client, ana, id_da_musica)
    client.post("/usuarios/ana/follow", headers=leitor)
    antes = client.get("/feed", headers=leitor).json()

    avisar(client, ana, r["id"], "de novo")

    depois = client.get("/feed", headers=leitor).json()
    assert depois == antes
    assert "comentario" not in set(depois["items"][0])  # o campo do aviso (não confundir com `comentarios`, a contagem)


def test_exigem_login_e_aparecem_na_documentacao_da_api(client, logar, id_da_musica):
    ana = logar("ana")
    r = criar(client, ana, id_da_musica)

    assert client.get("/feed/reescutas").status_code == 401
    assert client.get(f"/posts/{r['id']}/reescutas").status_code == 401
    rotas = client.get("/openapi.json").json()["paths"]
    assert "post" in rotas["/posts/{post_id}/reescutas"] and "get" in rotas["/feed/reescutas"]
