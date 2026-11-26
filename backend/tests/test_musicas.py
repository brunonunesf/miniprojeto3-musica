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


def test_capas_ausentes_nulas_e_validas_na_importacao(client, logar, monkeypatch):
    import copy
    from catalogo_musical import carregar_catalogo, validar_catalogo

    ana = logar('ana')
    originais = carregar_catalogo()
    registros = copy.deepcopy(originais)
    registros[0].pop('capa_url')
    registros[1]['capa_url'] = None
    # Exercita URL >300 caracteres, até o limite aceito de 2048.
    prefixo = 'https://images.example.com/'
    url = prefixo + 'a' * (2048 - len(prefixo))
    registros[2]['capa_url'] = url
    registros = validar_catalogo(registros)
    monkeypatch.setattr(service, 'carregar_catalogo', lambda: copy.deepcopy(registros))
    antes = client.get('/musicas?limit=100', headers=ana).json()['items']
    ids = {m['chave_catalogo']: m['id'] for m in antes}
    with SessionLocal() as db:
        assert service.importar_catalogo(db) == 0
        assert service.importar_catalogo(db) == 0
    depois = client.get('/musicas?limit=100', headers=ana)
    assert depois.status_code == 200
    por_chave = {m['chave_catalogo']: m for m in depois.json()['items']}
    assert por_chave[registros[0]['chave_catalogo']]['capa_url'] == ''
    assert por_chave[registros[1]['chave_catalogo']]['capa_url'] == ''
    com_capa = por_chave[registros[2]['chave_catalogo']]
    assert com_capa['capa_url'] == url
    assert client.get(f"/musicas/{com_capa['id']}", headers=ana).json()['capa_url'] == url
    assert {k: m['id'] for k, m in por_chave.items()} == ids
    # Remover capa existente também não pode gravar NULL ou mudar a identidade.
    registros[2]['capa_url'] = None
    with SessionLocal() as db:
        assert service.importar_catalogo(db) == 0
    assert client.get(f"/musicas/{com_capa['id']}", headers=ana).json()['capa_url'] == ''
    assert originais[2]['capa_url'] is None


def test_reiniciar_aplicacao_preserva_catalogo_e_credenciais(client, logar):
    from fastapi.testclient import TestClient
    from app.main import app

    ana = logar('ana')
    antes = client.get('/musicas?limit=100', headers=ana).json()
    # O banco não é apagado entre inicializações: reproduz o erro da segunda subida.
    with TestClient(app) as segunda_subida:
        resposta = segunda_subida.get('/musicas?limit=100', headers=ana)
        assert resposta.status_code == 200
        assert resposta.json() == antes
        assert segunda_subida.post('/auth/login', json={
            'username': 'ana', 'password': 'senha-forte-123',
        }).status_code == 200
