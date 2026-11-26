"""Reviews derivadas e a árvore de recomendações (issue #10)."""

from sqlalchemy import text

from app.core.floresta import floresta
from app.db import SessionLocal, atualizar_esquema_antigo, engine
from app.services import arvores as servico_arvores

MARE = "demo-mare-original"


def avaliar(client, quem, id_da_musica, chave=MARE, texto="", origem_id=None, nota=8):
    corpo = {"musica_id": id_da_musica(quem, chave), "nota": nota, "texto": texto}
    if origem_id is not None:
        corpo["origem_id"] = origem_id
    return client.post("/posts", json=corpo, headers=quem)


def criar(client, quem, id_da_musica, chave=MARE, texto="", origem_id=None):
    r = avaliar(client, quem, id_da_musica, chave, texto, origem_id)
    assert r.status_code == 201, r.text
    return r.json()


def arvore(client, quem, post_id):
    r = client.get(f"/posts/{post_id}/arvore", headers=quem)
    assert r.status_code == 200, r.text
    return r.json()


def forma(no):
    """A árvore reduzida a (id, [filhos]) para comparar o desenho."""
    return (no["id"], [forma(f) for f in no["filhos"]])


def corrente(client, logar, id_da_musica):
    """Ana → Júlia → Pedro, o exemplo do produto."""
    ana, julia, pedro = logar("ana", "Ana"), logar("julia", "Júlia"), logar("pedro", "Pedro")
    a = criar(client, ana, id_da_musica, texto="indico")
    j = criar(client, julia, id_da_musica, texto="vim pela Ana", origem_id=a["id"])
    p = criar(client, pedro, id_da_musica, texto="vim pela Júlia", origem_id=j["id"])
    return ana, julia, pedro, a, j, p


# ---------- criação ----------


def test_corrente_de_tres_niveis(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)

    esperada = (a["id"], [(j["id"], [(p["id"], [])])])
    for qualquer in (a, j, p):  # a árvore é a mesma, de qualquer review dela
        assert forma(arvore(client, ana, qualquer["id"])["raiz"]) == esperada


def test_derivada_traz_a_origem(client, logar, id_da_musica):
    ana, julia, _, a, j, _ = corrente(client, logar, id_da_musica)

    assert j["origem_id"] == a["id"]
    assert j["origem"]["id"] == a["id"] and j["origem"]["autor"]["username"] == "ana"
    assert a["origem_id"] is None and a["origem"] is None
    assert client.get(f"/posts/{j['id']}", headers=julia).json()["origem"]["autor"]["name"] == "Ana"


def test_dois_ramos_a_partir_da_mesma_raiz(client, logar, id_da_musica):
    ana, julia, pedro, a, j, _ = corrente(client, logar, id_da_musica)
    caio = logar("caio")
    c = criar(client, caio, id_da_musica, texto="também pela Ana", origem_id=a["id"])

    raiz = arvore(client, ana, a["id"])["raiz"]

    assert [f["id"] for f in raiz["filhos"]] == [j["id"], c["id"]]  # em ordem de publicação


def test_raiz_isolada_e_raizes_distintas_da_mesma_musica(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    a = criar(client, ana, id_da_musica)
    b = criar(client, bia, id_da_musica)  # independente: mesma música, sem origem

    assert forma(arvore(client, ana, a["id"])["raiz"]) == (a["id"], [])
    assert forma(arvore(client, ana, b["id"])["raiz"]) == (b["id"], [])


def test_no_traz_autor_e_nota_e_a_arvore_traz_a_musica(client, logar, id_da_musica):
    ana, _, _, a, _, _ = corrente(client, logar, id_da_musica)

    resposta = arvore(client, ana, a["id"])

    assert resposta["musica"]["chave_catalogo"] == MARE
    assert resposta["raiz"]["autor"] == {"username": "ana", "name": "Ana"}
    assert resposta["raiz"]["nota"] == 8 and resposta["raiz"]["apagada"] is False
    assert resposta["truncada"] is False


# ---------- regras da derivada ----------


def test_derivada_exige_texto_proprio(client, logar, id_da_musica):
    ana, julia = logar("ana"), logar("julia")
    a = criar(client, ana, id_da_musica)

    for texto in ["", "   "]:
        assert avaliar(client, julia, id_da_musica, texto=texto, origem_id=a["id"]).status_code == 422

    # uma raiz continua podendo ser só a nota
    assert avaliar(client, julia, id_da_musica).status_code == 201


def test_derivada_nao_pode_ficar_sem_texto_ao_editar(client, logar, id_da_musica):
    ana, julia = logar("ana"), logar("julia")
    a = criar(client, ana, id_da_musica)
    j = criar(client, julia, id_da_musica, texto="com texto", origem_id=a["id"])

    assert client.patch(f"/posts/{j['id']}", json={"texto": ""}, headers=julia).status_code == 422
    assert client.patch(f"/posts/{j['id']}", json={"nota": 3}, headers=julia).status_code == 200  # só a nota
    # a raiz pode ficar sem texto
    assert client.patch(f"/posts/{a['id']}", json={"texto": ""}, headers=ana).status_code == 200


def test_origem_inexistente_de_outra_musica_ou_apagada(client, logar, id_da_musica):
    ana, julia = logar("ana"), logar("julia")
    a = criar(client, ana, id_da_musica, MARE)

    assert avaliar(client, julia, id_da_musica, texto="x", origem_id=999).status_code == 422
    # origem de outra música: a ligação só vale dentro da mesma gravação
    assert avaliar(client, julia, id_da_musica, "demo-horizonte-original", "x", a["id"]).status_code == 422

    client.delete(f"/posts/{a['id']}", headers=ana)
    assert avaliar(client, julia, id_da_musica, texto="x", origem_id=a["id"]).status_code == 422


def test_uma_review_ativa_por_pessoa_e_musica_tambem_nas_derivadas(client, logar, id_da_musica):
    ana, julia = logar("ana"), logar("julia")
    a = criar(client, ana, id_da_musica)
    criar(client, julia, id_da_musica, texto="vim pela Ana", origem_id=a["id"])

    # Julia não faz outra; Ana não deriva da própria (já tem review desta música)
    assert avaliar(client, julia, id_da_musica, texto="de novo", origem_id=a["id"]).status_code == 409
    assert avaliar(client, ana, id_da_musica, texto="eu mesma", origem_id=a["id"]).status_code == 409


def test_a_edicao_nao_muda_a_origem(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)

    client.patch(f"/posts/{p['id']}", json={"nota": 5, "origem_id": a["id"]}, headers=pedro)

    assert client.get(f"/posts/{p['id']}", headers=pedro).json()["origem_id"] == j["id"]


def test_falha_de_gravacao_nao_deixa_no_na_arvore(client, logar, id_da_musica):
    ana, julia = logar("ana"), logar("julia")
    a = criar(client, ana, id_da_musica)
    criar(client, julia, id_da_musica, texto="vim pela Ana", origem_id=a["id"])

    assert avaliar(client, julia, id_da_musica, texto="repetida", origem_id=a["id"]).status_code == 409
    assert avaliar(client, julia, id_da_musica, texto="x", origem_id=999).status_code == 422

    assert len(arvore(client, ana, a["id"])["raiz"]["filhos"]) == 1  # só a primeira derivada


# ---------- exclusão ----------


def test_apagar_uma_do_meio_preserva_os_ramos(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)

    assert client.delete(f"/posts/{j['id']}", headers=julia).status_code == 204

    raiz = arvore(client, ana, p["id"])["raiz"]
    assert forma(raiz) == (a["id"], [(j["id"], [(p["id"], [])])])
    no_j = raiz["filhos"][0]
    assert (no_j["apagada"], no_j["autor"], no_j["nota"]) == (True, None, None)  # sem conteúdo nem autoria
    assert no_j["filhos"][0]["autor"]["username"] == "pedro"  # o descendente continua com os dados dele
    assert client.get(f"/posts/{j['id']}", headers=ana).status_code == 404


def test_a_derivada_de_origem_apagada_continua_ligada(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    client.delete(f"/posts/{j['id']}", headers=julia)

    pedro_visto = client.get(f"/posts/{p['id']}", headers=pedro).json()

    assert pedro_visto["origem_id"] == j["id"]  # ainda aponta para o lugar dela
    assert pedro_visto["origem"] is None  # mas não há mais review para mostrar


def test_apagar_a_raiz_e_recomecar_e_uma_raiz_nova(client, logar, id_da_musica):
    ana, julia, _, a, j, p = corrente(client, logar, id_da_musica)

    client.delete(f"/posts/{a['id']}", headers=ana)
    antiga = arvore(client, julia, j["id"])["raiz"]
    assert (antiga["id"], antiga["apagada"]) == (a["id"], True)

    nova = criar(client, ana, id_da_musica, texto="de novo")  # mesma pessoa e música
    assert nova["id"] != a["id"] and nova["origem_id"] is None
    assert forma(arvore(client, ana, nova["id"])["raiz"]) == (nova["id"], [])  # sem ligação com a antiga
    assert forma(arvore(client, julia, j["id"])["raiz"]) == (a["id"], [(j["id"], [(p["id"], [])])])


def test_apagar_uma_folha_deixa_o_lugar_dela(client, logar, id_da_musica):
    ana, _, pedro, a, j, p = corrente(client, logar, id_da_musica)

    client.delete(f"/posts/{p['id']}", headers=pedro)

    folha = arvore(client, ana, a["id"])["raiz"]["filhos"][0]["filhos"][0]
    assert (folha["id"], folha["apagada"], folha["filhos"]) == (p["id"], True, [])


def test_curtir_e_comentar_numa_review_apagada_devolve_404(client, logar, id_da_musica):
    ana, julia, _, _, j, _ = corrente(client, logar, id_da_musica)
    client.delete(f"/posts/{j['id']}", headers=julia)

    assert client.post(f"/posts/{j['id']}/curtir", headers=ana).status_code == 404
    assert client.post(f"/posts/{j['id']}/comentarios", json={"texto": "oi"}, headers=ana).status_code == 404


# ---------- leitura ----------


def test_feed_traz_a_origem_das_derivadas(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    leitor = logar("leitor")
    for quem in ("julia", "pedro"):
        client.post(f"/usuarios/{quem}/follow", headers=leitor)

    itens = {i["id"]: i for i in client.get("/feed", headers=leitor).json()["items"]}

    assert itens[j["id"]]["origem"]["autor"]["username"] == "ana"
    assert itens[p["id"]]["origem"]["autor"]["username"] == "julia"


def test_arvore_com_limite_de_leitura(client, logar, id_da_musica, monkeypatch):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    monkeypatch.setattr(servico_arvores, "LIMITE_DA_ARVORE", 1)  # a raiz e mais 1 review

    resposta = arvore(client, ana, a["id"])

    assert resposta["truncada"] is True
    assert forma(resposta["raiz"]) == (a["id"], [(j["id"], [])])  # o resto fica de fora

    monkeypatch.setattr(servico_arvores, "LIMITE_DA_ARVORE", 2)  # cabe tudo: a raiz e as 2 derivadas
    completa = arvore(client, ana, a["id"])
    assert completa["truncada"] is False
    assert forma(completa["raiz"]) == (a["id"], [(j["id"], [(p["id"], [])])])


def test_arvore_inexistente_login_e_id_gigante(client, logar):
    ana = logar("ana")

    assert client.get("/posts/999/arvore", headers=ana).status_code == 404
    assert client.get("/posts/1/arvore").status_code == 401
    assert client.get(f"/posts/{10**30}/arvore", headers=ana).status_code == 422
    assert client.post("/posts", json={"musica_id": 1, "nota": 5, "texto": "x", "origem_id": 10**30},
                       headers=ana).status_code == 422


# ---------- reinício ----------


def test_reiniciar_reconstroi_a_mesma_arvore(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    client.delete(f"/posts/{j['id']}", headers=julia)  # inclui uma review apagada
    antes = arvore(client, ana, a["id"])

    floresta.reconstruir([])  # a memória zera no reinício
    with SessionLocal() as db:
        servico_arvores.reconstruir(db)

    assert arvore(client, ana, a["id"]) == antes


def test_banco_antigo_sem_a_coluna_ganha_a_coluna_e_continua_funcionando(client, logar, id_da_musica):
    ana = logar("ana")
    with engine.begin() as conexao:  # volta ao formato de antes da árvore
        conexao.execute(text("DROP INDEX IF EXISTS ix_posts_origem_id"))
        conexao.execute(text("ALTER TABLE posts DROP COLUMN origem_id"))

    atualizar_esquema_antigo()
    atualizar_esquema_antigo()  # repetir é seguro

    a = criar(client, ana, id_da_musica)
    assert a["origem_id"] is None
    assert forma(arvore(client, ana, a["id"])["raiz"]) == (a["id"], [])
