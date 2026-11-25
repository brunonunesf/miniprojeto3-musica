from app.db import SessionLocal
from app.services import musicas as service


def test_catalogo_exige_login(client):
    assert client.get("/musicas").status_code == 401
    assert client.get("/musicas/1").status_code == 401


def test_catalogo_vem_carregado_na_subida(client, logar):
    ana = logar("ana")

    r = client.get("/musicas", headers=ana)

    assert r.status_code == 200
    assert r.json()["total"] == 6
    musica = r.json()["items"][0]
    assert {"id", "chave_catalogo", "titulo", "artista", "tipo_versao", "generos", "tags", "capa_url"} <= musica.keys()


def test_busca_ignora_caixa_e_espacos_sobrando(client, logar):
    ana = logar("ana")

    r = client.get("/musicas?q=  HORIZONTE  ", headers=ana)
    assert r.json()["total"] == 5

    r = client.get("/musicas?q=lua MARÉ", headers=ana)  # termos de campos diferentes
    assert r.json()["total"] == 1

    # sem acento também acha: "mare" encontra "Maré"
    assert client.get("/musicas?q=mare", headers=ana).json()["total"] == 1
    assert client.get("/musicas?q=MARE", headers=ana).json()["total"] == 1

    assert client.get("/musicas?q=inexistente", headers=ana).json()["items"] == []


def test_paginacao(client, logar):
    ana = logar("ana")

    r = client.get("/musicas?offset=2&limit=2", headers=ana).json()

    assert (r["offset"], r["limit"], len(r["items"]), r["total"]) == (2, 2, 2, 6)


def test_versoes_do_mesmo_titulo_sao_itens_distintos(client, logar):
    ana = logar("ana")

    items = client.get("/musicas?q=aurora", headers=ana).json()["items"]

    assert {m["tipo_versao"] for m in items} == {"original", "remix", "ao_vivo", "remaster"}
    assert len({m["id"] for m in items}) == 4


def test_consultar_musica(client, logar):
    ana = logar("ana")
    musica = client.get("/musicas?q=maré", headers=ana).json()["items"][0]

    assert client.get(f"/musicas/{musica['id']}", headers=ana).json() == musica
    assert client.get("/musicas/99999", headers=ana).status_code == 404


def test_parametros_invalidos_devolvem_422(client, logar):
    ana = logar("ana")

    enorme = 10**30  # maior que o inteiro do banco: deve ser 422, não estourar em 500
    caminhos = ["/musicas/0", f"/musicas/{enorme}", "/musicas?limit=101", "/musicas?limit=0", "/musicas?offset=-1"]
    for caminho in caminhos:
        assert client.get(caminho, headers=ana).status_code == 422


def test_importar_o_catalogo_de_novo_preserva_os_ids(client, logar):
    ana = logar("ana")
    antes = client.get("/musicas?limit=100", headers=ana).json()["items"]

    with SessionLocal() as db:
        assert service.importar_catalogo(db) == 0

    assert client.get("/musicas?limit=100", headers=ana).json()["items"] == antes


def test_importar_trata_a_capa_opcional_do_catalogo(client, logar, monkeypatch):
    ana = logar("ana")
    base = {
        "tipo_versao": "original",
        "descricao_versao": "",
        "generos": ["indie"],
        "tags": ["calma"],
    }
    catalogo = [
        {**base, "chave_catalogo": "sem-capa", "titulo": "Sem Capa", "artista": "A", "capa_url": None},
        {**base, "chave_catalogo": "com-capa", "titulo": "Com Capa", "artista": "B", "capa_url": "https://exemplo.com/c.jpg"},
    ]
    monkeypatch.setattr(service, "carregar_catalogo", lambda: catalogo)

    with SessionLocal() as db:
        assert service.importar_catalogo(db) == 2  # catálogo com capa None não derruba a importação

    achadas = {m["titulo"]: m["capa_url"] for m in client.get("/musicas?q=capa", headers=ana).json()["items"]}
    assert achadas == {"Sem Capa": "", "Com Capa": "https://exemplo.com/c.jpg"}
