"""Corrigir a origem de uma review derivada (issue #10): PATCH /posts/{id}/origem.

Cenário base: Ana e Bia têm reviews-raiz da mesma música; Júlia derivou de Ana, Pedro de Júlia, Caio de Pedro.
Pontos (4/2/1): a derivada de Júlia dá 4 a Ana; a de Pedro dá 4 a Júlia e 2 a Ana; a de Caio dá 4 a Pedro,
2 a Júlia e 1 a Ana. Uma curtida em quem está na ponta da corrente também pontua a corrente inteira.
"""

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func, select

from app.core.floresta import floresta
from app.core.reputacao import reputacao_reviews
from app.db import SessionLocal
from app.models.evento_reputacao import EventoReputacao
from app.services import arvores as servico_arvores
from app.services import reputacao as servico

MARE = "demo-mare-original"
OUTRA = "demo-horizonte-original"


def criar(client, quem, id_da_musica, chave=MARE, texto="", origem_id=None):
    corpo = {"musica_id": id_da_musica(quem, chave), "nota": 8, "texto": texto}
    if origem_id is not None:
        corpo["origem_id"] = origem_id
    r = client.post("/posts", json=corpo, headers=quem)
    assert r.status_code == 201, r.text
    return r.json()


def pontos(client, leitor, *usernames):
    return {u: client.get(f"/usuarios/{u}", headers=leitor).json()["reputacao"] for u in usernames}


def trocar(client, quem, post_id, origem_id):
    return client.patch(f"/posts/{post_id}/origem", json={"origem_id": origem_id}, headers=quem)


def cenario(client, logar, id_da_musica):
    pessoas = {n: logar(n, n.capitalize()) for n in ("ana", "bia", "julia", "pedro", "caio")}
    a = criar(client, pessoas["ana"], id_da_musica, texto="indico")
    b = criar(client, pessoas["bia"], id_da_musica, texto="indico também")
    j = criar(client, pessoas["julia"], id_da_musica, texto="pela Ana", origem_id=a["id"])
    p = criar(client, pessoas["pedro"], id_da_musica, texto="pela Júlia", origem_id=j["id"])
    c = criar(client, pessoas["caio"], id_da_musica, texto="pelo Pedro", origem_id=p["id"])
    return pessoas, {"ana": a, "bia": b, "julia": j, "pedro": p, "caio": c}


def arvore(client, quem, post_id):
    r = client.get(f"/posts/{post_id}/arvore", headers=quem)
    assert r.status_code == 200, r.text
    return r.json()["raiz"]


def forma(no):
    return (no["id"], sorted(forma(f) for f in no["filhos"]))


def refazer_tudo_como_no_reinicio():
    floresta.reconstruir([])
    reputacao_reviews.reconstruir(floresta, [])
    with SessionLocal() as db:
        servico_arvores.reconstruir(db)
        servico.sincronizar_eventos(db)
        servico.reconstruir(db)


# ---------- a troca ----------


def test_o_autor_troca_a_origem_e_a_resposta_ja_traz_a_nova(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)

    resposta = trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"])

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["id"] == r["pedro"]["id"] and corpo["origem_id"] == r["bia"]["id"]
    assert corpo["origem"]["autor"]["username"] == "bia"
    # e quem lê a review depois vê a mesma coisa
    assert client.get(f"/posts/{r['pedro']['id']}", headers=p["ana"]).json()["origem_id"] == r["bia"]["id"]


def test_a_subarvore_vai_junto_e_a_arvore_antiga_perde_o_ramo(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    ana, bia, julia, pedro, caio = (r[n]["id"] for n in ("ana", "bia", "julia", "pedro", "caio"))
    assert forma(arvore(client, p["ana"], ana)) == (ana, [(julia, [(pedro, [(caio, [])])])])

    trocar(client, p["pedro"], pedro, bia)

    # o Caio (descendente do Pedro) acompanha o Pedro para a árvore da Bia
    assert forma(arvore(client, p["ana"], ana)) == (ana, [(julia, [])])
    assert forma(arvore(client, p["bia"], bia)) == (bia, [(pedro, [(caio, [])])])
    assert forma(arvore(client, p["caio"], caio)) == (bia, [(pedro, [(caio, [])])])  # lida a partir da ponta


def test_trocar_para_a_origem_atual_nao_muda_nada(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    antes = pontos(client, p["ana"], "ana", "bia", "julia", "pedro")

    resposta = trocar(client, p["pedro"], r["pedro"]["id"], r["julia"]["id"])

    assert resposta.status_code == 200 and resposta.json()["origem_id"] == r["julia"]["id"]
    assert pontos(client, p["ana"], "ana", "bia", "julia", "pedro") == antes


def test_trocar_para_cima_e_para_o_lado_na_mesma_corrente(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)

    # o Pedro estava na Júlia; passa direto para a Ana (um nível acima), com o Caio junto
    assert trocar(client, p["pedro"], r["pedro"]["id"], r["ana"]["id"]).status_code == 200

    ana = r["ana"]["id"]
    assert forma(arvore(client, p["ana"], ana)) == (ana, [(r["julia"]["id"], []), (r["pedro"]["id"], [(r["caio"]["id"], [])])])


# ---------- reputação ----------


def test_os_pontos_acompanham_a_corrente_nova_e_voltam_se_a_troca_for_desfeita(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.post(f"/posts/{r['pedro']['id']}/curtir", headers=leitor)  # curtida no Pedro: 4 Pedro, 2 Júlia, 1 Ana
    nomes = ("ana", "bia", "julia", "pedro", "caio")
    # derivadas: Júlia(Ana 4) + Pedro(Júlia 4, Ana 2) + Caio(Pedro 4, Júlia 2, Ana 1); curtida: Pedro 4, Júlia 2, Ana 1
    antes = {"ana": 8, "bia": 0, "julia": 8, "pedro": 8, "caio": 0}
    assert pontos(client, leitor, *nomes) == antes

    assert trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"]).status_code == 200

    # a corrente do Pedro agora é Bia → Pedro: derivada do Pedro dá 4 à Bia; derivada do Caio dá 4 ao Pedro e 2 à Bia;
    # a curtida no Pedro dá 4 ao Pedro e 2 à Bia. A Ana fica só com o que veio da Júlia (4) e a Júlia perde tudo do ramo.
    assert pontos(client, leitor, *nomes) == {"ana": 4, "bia": 8, "julia": 0, "pedro": 8, "caio": 0}

    assert trocar(client, p["pedro"], r["pedro"]["id"], r["julia"]["id"]).status_code == 200
    assert pontos(client, leitor, *nomes) == antes  # desfazer devolve exatamente o que era


def test_mover_a_origem_nao_cria_evento_pontuavel(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.post(f"/posts/{r['pedro']['id']}/curtir", headers=leitor)
    with SessionLocal() as db:
        antes = sorted(db.scalars(select(EventoReputacao.chave)))

    trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"])
    trocar(client, p["pedro"], r["pedro"]["id"], r["ana"]["id"])

    with SessionLocal() as db:
        assert sorted(db.scalars(select(EventoReputacao.chave))) == antes  # os mesmos fatos, nenhum novo


def test_reiniciar_depois_da_troca_da_o_mesmo_resultado(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.post(f"/posts/{r['caio']['id']}/curtir", headers=leitor)
    trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"])
    nomes = ("ana", "bia", "julia", "pedro", "caio")
    antes = pontos(client, leitor, *nomes)
    arvore_antes = forma(arvore(client, leitor, r["bia"]["id"]))

    refazer_tudo_como_no_reinicio()

    assert pontos(client, leitor, *nomes) == antes
    assert forma(arvore(client, leitor, r["bia"]["id"])) == arvore_antes  # o banco guardou a troca


def test_origem_apagada_pode_ser_corrigida_e_os_creditos_dela_saem_da_corrente_do_ramo(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    nomes = ("ana", "bia", "julia", "pedro", "caio")
    client.delete(f"/posts/{r['julia']['id']}", headers=p["julia"])  # a origem do Pedro é apagada
    leitor = logar("leitor")
    # os créditos já dados são conservados: ana 4+2+1=7, julia 4+2=6, pedro 4
    assert pontos(client, leitor, *nomes) == {"ana": 7, "bia": 0, "julia": 6, "pedro": 4, "caio": 0}

    resposta = trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"])

    assert resposta.status_code == 200, resposta.text
    # a derivada da Júlia continua dando 4 à Ana; as do ramo do Pedro agora creditam a Bia (4 + 2) e o Pedro (4)
    assert pontos(client, leitor, *nomes) == {"ana": 4, "bia": 6, "julia": 0, "pedro": 4, "caio": 0}
    assert forma(arvore(client, leitor, r["caio"]["id"]))[0] == r["bia"]["id"]


def test_o_feed_mostra_a_origem_nova(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.post("/usuarios/pedro/follow", headers=leitor)

    trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"])

    item = next(i for i in client.get("/feed", headers=leitor).json()["items"] if i["id"] == r["pedro"]["id"])
    assert item["origem_id"] == r["bia"]["id"] and item["origem"]["autor"]["username"] == "bia"


# ---------- o que é recusado ----------


def test_so_o_autor_troca_e_exige_login(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)

    assert trocar(client, p["ana"], r["pedro"]["id"], r["bia"]["id"]).status_code == 403
    assert client.patch(f"/posts/{r['pedro']['id']}/origem", json={"origem_id": r["bia"]["id"]}).status_code == 401
    assert client.get(f"/posts/{r['pedro']['id']}", headers=p["ana"]).json()["origem_id"] == r["julia"]["id"]


def test_review_inexistente_da_404(client, logar):
    ana = logar("ana")

    assert trocar(client, ana, 9999, 1).status_code == 404


def test_raiz_nao_ganha_origem(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)

    resposta = trocar(client, p["bia"], r["bia"]["id"], r["ana"]["id"])

    assert resposta.status_code == 422 and "derivada" in resposta.json()["detail"]
    assert client.get(f"/posts/{r['bia']['id']}", headers=p["bia"]).json()["origem_id"] is None


def test_a_propria_review_e_os_descendentes_criariam_ciclo(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)

    for destino in (r["julia"]["id"], r["pedro"]["id"], r["caio"]["id"]):  # ela mesma, o filho e o neto
        resposta = trocar(client, p["julia"], r["julia"]["id"], destino)
        assert resposta.status_code == 422, (destino, resposta.text)
    assert client.get(f"/posts/{r['julia']['id']}", headers=p["ana"]).json()["origem_id"] == r["ana"]["id"]
    assert pontos(client, p["ana"], "ana", "julia", "pedro") == {"ana": 7, "julia": 6, "pedro": 4}  # nada mudou


def test_origem_inexistente_apagada_ou_de_outra_musica_e_recusada(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    apagada = criar(client, logar("dani"), id_da_musica, texto="x")
    client.delete(f"/posts/{apagada['id']}", headers=logar_depois(client, "dani"))
    de_outra_musica = criar(client, p["bia"], id_da_musica, chave=OUTRA)

    for destino in (9999, apagada["id"], de_outra_musica["id"]):
        assert trocar(client, p["pedro"], r["pedro"]["id"], destino).status_code == 422, destino


def logar_depois(client, username):
    from tests.conftest import SENHA_PADRAO

    token = client.post("/auth/login", json={"username": username, "password": SENHA_PADRAO}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_corpo_e_ids_invalidos_dao_422(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    url = f"/posts/{r['pedro']['id']}/origem"

    for corpo in ({}, {"origem_id": 0}, {"origem_id": -1}, {"origem_id": "x"}, {"origem_id": 2**70}, {"origem_id": None}):
        assert client.patch(url, json=corpo, headers=p["pedro"]).status_code == 422, corpo
    assert client.patch(f"/posts/{2**70}/origem", json={"origem_id": 1}, headers=p["pedro"]).status_code == 422


def test_a_tela_detecta_a_rota_pela_documentacao_da_api(client):
    rotas = client.get("/openapi.json").json()["paths"]

    assert "patch" in rotas["/posts/{post_id}/origem"]


# ---------- concorrência ----------


def test_trocas_simultaneas_deixam_banco_memoria_e_pontos_coerentes(client, logar, id_da_musica):
    p, r = cenario(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.post(f"/posts/{r['caio']['id']}/curtir", headers=leitor)
    alvos = [r["ana"]["id"], r["bia"]["id"], r["julia"]["id"]]

    def trocar_varias(quem, post_id, destinos):
        return [trocar(client, quem, post_id, d).status_code for d in destinos]

    with ThreadPoolExecutor(max_workers=2) as pool:
        # o Pedro anda entre origens possíveis, e a Júlia entre as suas (Ana ou Bia); os dois mexem na mesma árvore
        a = pool.submit(trocar_varias, p["pedro"], r["pedro"]["id"], (alvos * 4)[:10])
        b = pool.submit(trocar_varias, p["julia"], r["julia"]["id"], [r["bia"]["id"], r["ana"]["id"]] * 5)
        codigos = a.result() + b.result()

    assert set(codigos) <= {200, 409, 422}  # nunca 500; 422 se virou ciclo na hora, 409 se a review mudou no meio
    nomes = ("ana", "bia", "julia", "pedro", "caio")
    depois = pontos(client, leitor, *nomes)
    forma_antes = [forma(arvore(client, leitor, r[n]["id"])) for n in nomes]

    refazer_tudo_como_no_reinicio()  # o banco é a verdade: refazer tudo dele dá o mesmo que a memória tinha

    assert pontos(client, leitor, *nomes) == depois
    assert [forma(arvore(client, leitor, r[n]["id"])) for n in nomes] == forma_antes
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(EventoReputacao)) == 4  # 3 derivadas + 1 curtida, nada a mais


# ---------- o meio da operação: outra requisição mexe na mesma review ----------


def _mexer_no_meio(monkeypatch, acao):
    """Roda `acao(post_id)` no banco entre a validação da troca e a gravação, como faria outra requisição."""
    from app.services import posts as servico_posts

    original = servico_posts._preparar_troca

    def preparar_e_mexer(db, post_id, nova_origem_id):
        plano = original(db, post_id, nova_origem_id)
        with SessionLocal() as outra:
            acao(outra, post_id)
            outra.commit()
        return plano

    monkeypatch.setattr(servico_posts, "_preparar_troca", preparar_e_mexer)


def test_se_a_review_for_apagada_no_meio_da_troca_nada_e_gravado_e_a_resposta_e_409(client, logar, id_da_musica, monkeypatch):
    from sqlalchemy import delete

    from app.models.post import Post

    p, r = cenario(client, logar, id_da_musica)
    leitor = logar("leitor")
    antes = pontos(client, leitor, "ana", "bia", "julia", "pedro", "caio")
    _mexer_no_meio(monkeypatch, lambda db, post_id: db.execute(delete(Post).where(Post.id == post_id)))

    resposta = trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"])

    assert resposta.status_code == 409 and "tente de novo" in resposta.json()["detail"]
    assert pontos(client, leitor, "ana", "bia", "julia", "pedro", "caio") == antes  # nada foi refeito nem trocado
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(EventoReputacao)) == 3  # só as 3 derivadas de antes


def test_se_a_origem_mudar_no_meio_da_troca_prevalece_a_outra_e_a_resposta_e_409(client, logar, id_da_musica, monkeypatch):
    from sqlalchemy import update

    from app.models.post import Post

    p, r = cenario(client, logar, id_da_musica)
    ana = r["ana"]["id"]
    _mexer_no_meio(monkeypatch, lambda db, post_id: db.execute(update(Post).where(Post.id == post_id).values(origem_id=ana)))

    resposta = trocar(client, p["pedro"], r["pedro"]["id"], r["bia"]["id"])

    assert resposta.status_code == 409
    with SessionLocal() as db:
        assert db.get(Post, r["pedro"]["id"]).origem_id == ana  # a troca que chegou antes ficou, a nossa não foi gravada


# ---------- dados gravados por fora da API (um seed) ----------


def test_review_gravada_por_fora_e_desconhecida_da_arvore_e_refeita_a_partir_do_banco(client, logar, id_da_musica):
    from app.models.post import Post

    julia, bia, pedro = logar("julia"), logar("bia"), logar("pedro")
    ids = {u: client.get(f"/usuarios/{u}", headers=julia).json()["id"] for u in ("julia", "bia", "pedro")}
    musica = id_da_musica(julia, OUTRA)
    with SessionLocal() as db:  # como um seed que gravou direto no banco com o servidor ligado
        raiz_a = Post(texto="a", nota=7, autor_id=ids["bia"], musica_id=musica)
        raiz_b = Post(texto="b", nota=7, autor_id=ids["pedro"], musica_id=musica)
        db.add_all([raiz_a, raiz_b])
        db.flush()
        derivada = Post(texto="d", nota=7, autor_id=ids["julia"], musica_id=musica, origem_id=raiz_a.id)
        db.add(derivada)
        db.commit()
        a_id, b_id, d_id = raiz_a.id, raiz_b.id, derivada.id

    resposta = trocar(client, julia, d_id, b_id)  # a árvore em memória ainda não conhece nenhuma delas

    assert resposta.status_code == 200, resposta.text
    assert forma(arvore(client, julia, d_id)) == (b_id, [(d_id, [])])
    assert forma(arvore(client, julia, a_id)) == (a_id, [])
