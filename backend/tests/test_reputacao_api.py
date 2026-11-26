"""Reputação ligada à API (issue #10/#11): fórmula 4/2/1 do DECISIONS.md, com eventos guardados no banco."""

from sqlalchemy import func, select

from app.core.floresta import floresta
from app.core.reputacao import reputacao_reviews
from app.db import SessionLocal
from app.models.curtida import Curtida
from app.models.evento_reputacao import EventoReputacao
from app.models.post import Post
from app.services import arvores as servico_arvores
from app.services import reputacao as servico

MARE = "demo-mare-original"


def criar(client, quem, id_da_musica, chave=MARE, texto="", origem_id=None):
    corpo = {"musica_id": id_da_musica(quem, chave), "nota": 8, "texto": texto}
    if origem_id is not None:
        corpo["origem_id"] = origem_id
    r = client.post("/posts", json=corpo, headers=quem)
    assert r.status_code == 201, r.text
    return r.json()


def pontos(client, leitor, *usernames):
    return {u: client.get(f"/usuarios/{u}", headers=leitor).json()["reputacao"] for u in usernames}


def corrente(client, logar, id_da_musica):
    """Ana → Júlia → Pedro, o exemplo do DECISIONS.md."""
    ana, julia, pedro = logar("ana", "Ana"), logar("julia", "Júlia"), logar("pedro", "Pedro")
    a = criar(client, ana, id_da_musica, texto="indico")
    j = criar(client, julia, id_da_musica, texto="pela Ana", origem_id=a["id"])
    p = criar(client, pedro, id_da_musica, texto="pela Júlia", origem_id=j["id"])
    return ana, julia, pedro, a, j, p


def refazer_tudo_como_no_reinicio():
    """O que o startup faz: a memória zera e é refeita a partir do banco."""
    floresta.reconstruir([])
    reputacao_reviews.reconstruir(floresta, [])
    with SessionLocal() as db:
        servico_arvores.reconstruir(db)
        servico.sincronizar_eventos(db)
        servico.reconstruir(db)


# ---------- review derivada ----------


def test_publicar_uma_derivada_pontua_a_origem_e_os_ancestrais(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)

    # Júlia derivou de Ana: Ana +4. Pedro derivou de Júlia: Júlia +4 e Ana +2. O autor da nova não ganha.
    assert pontos(client, ana, "ana", "julia", "pedro") == {"ana": 6, "julia": 4, "pedro": 0}


def test_publicar_uma_raiz_nao_pontua_ninguem(client, logar, id_da_musica):
    ana = logar("ana")

    criar(client, ana, id_da_musica)

    assert pontos(client, ana, "ana") == {"ana": 0}


def test_o_quarto_nivel_nao_recebe(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    caio = logar("caio")

    criar(client, caio, id_da_musica, texto="pelo Pedro", origem_id=p["id"])

    # Caio derivou de Pedro: Pedro +4, Júlia +2, Ana +1 (só três níveis). Antes: ana 6, julia 4, pedro 0.
    assert pontos(client, ana, "ana", "julia", "pedro", "caio") == {"ana": 7, "julia": 6, "pedro": 4, "caio": 0}


# ---------- curtidas ----------


def test_curtida_de_outra_pessoa_pontua_o_autor_e_a_corrente(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    leitor = logar("leitor")

    client.post(f"/posts/{p['id']}/curtir", headers=leitor)

    # Pedro +4, Júlia +2, Ana +1, somados ao que a publicação das derivadas já tinha dado.
    assert pontos(client, ana, "ana", "julia", "pedro") == {"ana": 7, "julia": 6, "pedro": 4}


def test_curtida_de_raiz_pontua_so_o_autor(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    a = criar(client, ana, id_da_musica)

    client.post(f"/posts/{a['id']}/curtir", headers=bia)

    assert pontos(client, bia, "ana", "bia") == {"ana": 4, "bia": 0}


def test_curtida_propria_da_um_ponto_so_ao_autor_sem_propagar(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)

    client.post(f"/posts/{p['id']}/curtir", headers=pedro)  # Pedro curte a própria review

    assert pontos(client, ana, "ana", "julia", "pedro") == {"ana": 6, "julia": 4, "pedro": 1}


def test_curtir_de_novo_nao_pontua_de_novo(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    a = criar(client, ana, id_da_musica)

    for _ in range(3):
        client.post(f"/posts/{a['id']}/curtir", headers=bia)

    assert pontos(client, bia, "ana") == {"ana": 4}
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(EventoReputacao)) == 1  # um evento só


def test_descurtir_retira_exatamente_os_pontos_e_recurtir_concede_uma_vez(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    leitor = logar("leitor")
    antes = pontos(client, ana, "ana", "julia", "pedro")

    client.post(f"/posts/{p['id']}/curtir", headers=leitor)
    client.delete(f"/posts/{p['id']}/curtir", headers=leitor)
    assert pontos(client, ana, "ana", "julia", "pedro") == antes  # voltou ao que era
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(EventoReputacao).where(EventoReputacao.tipo == "curtida")) == 0

    client.post(f"/posts/{p['id']}/curtir", headers=leitor)
    client.post(f"/posts/{p['id']}/curtir", headers=leitor)
    assert pontos(client, ana, "ana", "julia", "pedro") == {"ana": 7, "julia": 6, "pedro": 4}  # uma vez só


def test_descurtir_o_que_nao_esta_curtido_nao_tira_pontos(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    a = criar(client, ana, id_da_musica)
    client.post(f"/posts/{a['id']}/curtir", headers=bia)

    for _ in range(3):
        client.delete(f"/posts/{a['id']}/curtir", headers=ana)  # Ana nunca curtiu a própria

    assert pontos(client, bia, "ana") == {"ana": 4}


def test_curtir_review_inexistente_nao_cria_evento(client, logar):
    ana = logar("ana")

    assert client.post("/posts/999/curtir", headers=ana).status_code == 404

    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(EventoReputacao)) == 0


# ---------- o que não pontua ----------


def test_comentar_seguir_e_editar_nao_pontuam(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    leitor = logar("leitor")
    antes = pontos(client, ana, "ana", "julia", "pedro")

    client.post(f"/posts/{p['id']}/comentarios", json={"texto": "oi"}, headers=leitor)
    client.post("/usuarios/pedro/follow", headers=leitor)
    client.patch(f"/posts/{p['id']}", json={"nota": 1, "texto": "mudei"}, headers=pedro)

    assert pontos(client, ana, "ana", "julia", "pedro") == antes


# ---------- exclusão ----------


def test_apagar_uma_review_conserva_os_creditos_ja_concedidos(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.post(f"/posts/{p['id']}/curtir", headers=leitor)
    antes = pontos(client, ana, "ana", "julia", "pedro")

    client.delete(f"/posts/{j['id']}", headers=julia)  # a do meio
    client.delete(f"/posts/{p['id']}", headers=pedro)  # a que foi curtida (as curtidas somem)

    assert pontos(client, ana, "ana", "julia", "pedro") == antes


def test_curtida_futura_continua_creditando_quem_apagou_a_review_de_origem(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.delete(f"/posts/{j['id']}", headers=julia)  # Júlia apaga a dela; a de Pedro continua ligada
    antes = pontos(client, ana, "ana", "julia", "pedro")

    client.post(f"/posts/{p['id']}/curtir", headers=leitor)

    # Pedro +4, e o registro apagado de Júlia ainda recebe +2, e Ana +1.
    depois = pontos(client, ana, "ana", "julia", "pedro")
    assert (depois["pedro"] - antes["pedro"], depois["julia"] - antes["julia"], depois["ana"] - antes["ana"]) == (4, 2, 1)


def test_apagar_a_derivada_conserva_os_pontos_que_ela_gerou(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    antes = pontos(client, ana, "ana", "julia")

    client.delete(f"/posts/{p['id']}", headers=pedro)

    assert pontos(client, ana, "ana", "julia") == antes


# ---------- reinício e dados de fora ----------


def test_reiniciar_reconstroi_os_mesmos_totais(client, logar, id_da_musica):
    ana, julia, pedro, a, j, p = corrente(client, logar, id_da_musica)
    leitor = logar("leitor")
    client.post(f"/posts/{p['id']}/curtir", headers=leitor)
    client.post(f"/posts/{j['id']}/curtir", headers=pedro)
    client.delete(f"/posts/{j['id']}", headers=julia)  # inclui uma review apagada
    antes = pontos(client, ana, "ana", "julia", "pedro", "leitor")

    refazer_tudo_como_no_reinicio()

    assert pontos(client, ana, "ana", "julia", "pedro", "leitor") == antes


def test_curtidas_e_derivadas_gravadas_por_fora_ganham_eventos_na_subida(client, logar, id_da_musica):
    """Um seed ou um banco antigo grava direto no banco: a subida cria os eventos que faltam."""
    ana, julia, pedro = logar("ana"), logar("julia"), logar("pedro")
    a = criar(client, ana, id_da_musica)
    ids = {u: client.get(f"/usuarios/{u}", headers=ana).json()["id"] for u in ("julia", "pedro")}
    with SessionLocal() as db:
        derivada = Post(
            texto="pela Ana", nota=7, autor_id=ids["julia"], musica_id=a["musica"]["id"], origem_id=a["id"]
        )
        db.add(derivada)
        db.flush()
        db.add(Curtida(usuario_id=ids["pedro"], post_id=derivada.id))  # Pedro curte a de Júlia
        db.commit()

    refazer_tudo_como_no_reinicio()

    # derivada: Ana +4; curtida de Pedro na review de Júlia: Júlia +4, Ana +2
    assert pontos(client, ana, "ana", "julia", "pedro") == {"ana": 6, "julia": 4, "pedro": 0}
    with SessionLocal() as db:
        assert servico.sincronizar_eventos(db) == 0  # repetir é seguro: nada novo


def test_dado_inconsistente_nao_derruba_a_reputacao(client, logar, id_da_musica):
    ana = logar("ana")
    a = criar(client, ana, id_da_musica)
    with SessionLocal() as db:
        db.add(EventoReputacao(chave="derivada:99999", tipo="derivada", review_id=99999))  # review que não existe
        db.commit()
        assert servico.tentar_reconstruir(db) is False  # avisa no log e segue

    assert client.get(f"/usuarios/ana", headers=ana).status_code == 200
    assert client.get(f"/posts/{a['id']}", headers=ana).status_code == 200


def test_perfil_traz_a_reputacao_de_qualquer_pessoa(client, logar, id_da_musica):
    ana, bia = logar("ana"), logar("bia")
    a = criar(client, ana, id_da_musica)
    client.post(f"/posts/{a['id']}/curtir", headers=bia)

    perfil = client.get("/usuarios/ana", headers=bia).json()

    assert perfil["reputacao"] == 4
    assert client.get("/usuarios/bia", headers=ana).json()["reputacao"] == 0
