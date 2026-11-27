import concurrent.futures
import json
import time

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models.catalogo_externo import AuditoriaCatalogo, ReferenciaExterna, RevisaoCorrespondencia, SolicitacaoInclusao
from app.models.musica import Musica
from app.models.post import Post
from app.schemas.catalogo_externo import FaixaExterna
from app.services import provedores_musicais, selecao_musical
from app.services.curadoria_catalogo import Operacao, executar
from app.services.identidade_musical import mesma_gravacao


def faixa(servico="spotify", id_externo="abc", **campos):
    dados = dict(servico=servico, id_externo=id_externo,
                 url=f"https://open.spotify.com/track/{id_externo}" if servico == "spotify" else f"https://www.deezer.com/track/{id_externo}",
                 titulo="Canção - Original Version", artistas=["Artista"], album="Álbum", duracao_ms=180000,
                 isrc="BRABC2600001", tipo_versao="original", descricao_versao="Original Version")
    return FaixaExterna(**(dados | campos))


@pytest.fixture(autouse=True)
def config(monkeypatch):
    monkeypatch.setenv("MUSICA_SELECTION_SECRET", "somente-testes-chave-com-mais-de-32-caracteres")
    monkeypatch.delenv("SPOTIFY_BUSCA_VALIDADA", raising=False)
    monkeypatch.delenv("DEEZER_BUSCA_VALIDADA", raising=False)


def usuario_id(client, auth):
    return client.get("/auth/eu", headers=auth).json()["id"]


def token(client, auth, faixas=None):
    return selecao_musical.assinar(faixas or [faixa()], usuario_id(client, auth))


def contagem(modelo):
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(modelo))


def fonte(monkeypatch, faixas):
    async def buscar(q):
        return [("spotify", "disponivel", [f for f in faixas if f.servico == "spotify"]),
                ("deezer", "disponivel", [f for f in faixas if f.servico == "deezer"])]
    monkeypatch.setattr(provedores_musicais, "buscar_fontes", buscar)


def test_buscar_agrupar_nao_persiste_e_publicar_atomico(client, logar, monkeypatch):
    auth = logar("externo")
    antes = contagem(Musica)
    fonte(monkeypatch, [faixa(), faixa("deezer", "123")])
    busca = client.get("/musicas/busca?q=Canção", headers=auth)
    assert busca.status_code == 200
    externo = busca.json()["items"][0]
    assert externo["fontes"] == ["spotify", "deezer"]
    assert contagem(Musica) == antes
    assert contagem(ReferenciaExterna) == contagem(RevisaoCorrespondencia) == 0
    # Selecionar não chama endpoint de escrita; só publicar grava os três objetos.
    resposta = client.post("/posts", headers=auth, json={"selecao_externa": externo["selecao_externa"], "nota": 8})
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["musica"]["generos"] == []
    assert contagem(Musica) == antes + 1
    assert contagem(ReferenciaExterna) == 2
    assert contagem(Post) == 1
    assert client.post("/posts", headers=auth, json={"selecao_externa": externo["selecao_externa"], "nota": 9}).status_code == 409
    assert contagem(Musica) == antes + 1


@pytest.mark.parametrize("alteracao", ["adulterado", "outro_usuario", "expirado", "nota", "origem"])
def test_falha_publicacao_nao_deixa_orfao(client, logar, monkeypatch, alteracao):
    auth = logar("falha")
    selecao = token(client, auth)
    dados = {"selecao_externa": selecao, "nota": 8}
    if alteracao == "adulterado":
        dados["selecao_externa"] += "0"
    elif alteracao == "outro_usuario":
        auth = logar("outro")
    elif alteracao == "expirado":
        monkeypatch.setattr(selecao_musical.time, "time", lambda: time_value)
    elif alteracao == "nota":
        dados["nota"] = 99
    elif alteracao == "origem":
        dados.update(origem_id=9999, texto="Minha análise")
    antes = contagem(Musica)
    resposta = client.post("/posts", headers=auth, json=dados)
    assert resposta.status_code == 422, resposta.text
    assert contagem(Musica) == antes
    assert contagem(Post) == contagem(ReferenciaExterna) == 0


time_value = time.time() + 86400


def test_erro_commit_reverte_musica_e_referencias(client, logar, monkeypatch):
    from sqlalchemy.orm import Session
    auth = logar("rollback")
    selecao = token(client, auth)
    antes = contagem(Musica)
    original = Session.commit
    def falhar(db):
        if any(isinstance(x, Post) for x in db.new):
            raise RuntimeError("falha simulada na gravação")
        return original(db)
    monkeypatch.setattr(Session, "commit", falhar)
    with pytest.raises(RuntimeError):
        client.post("/posts", headers=auth, json={"selecao_externa": selecao, "nota": 8})
    assert contagem(Musica) == antes
    assert contagem(ReferenciaExterna) == contagem(Post) == 0


@pytest.mark.parametrize("cruzada", [False, True])
def test_concorrencia_reutiliza_identidade(client, logar, cruzada):
    a, b = logar("concorrente_a"), logar("concorrente_b")
    tokens = [(a, token(client, a)), (b, token(client, b, [faixa("deezer", "1")] if cruzada else None))]
    def publicar(par):
        auth, selecao = par
        return client.post("/posts", headers=auth, json={"selecao_externa": selecao, "nota": 7})
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        respostas = list(pool.map(publicar, tokens))
    assert [r.status_code for r in respostas] == [201, 201]
    assert len({r.json()["musica"]["id"] for r in respostas}) == 1
    assert contagem(ReferenciaExterna) == (2 if cruzada else 1)


@pytest.mark.parametrize("mudanca", [dict(isrc=""), dict(tipo_versao="desconhecida"), dict(duracao_ms=183000),
                                    dict(artistas=["Outro"]), dict(tipo_versao="remix"), dict(descricao_versao="Outra edição")])
def test_matching_incompleto_divergente_permanece_separado(mudanca):
    assert not mesma_gravacao(faixa(), faixa("deezer", "1", **mudanca))


def test_matching_normaliza_nomes_mas_nao_usa_so_isrc():
    assert mesma_gravacao(faixa(artistas=["Ártista"]), faixa("deezer", "1", artistas=["ARTISTA"], duracao_ms=182000))
    assert not mesma_gravacao(faixa(), faixa("deezer", "1", titulo="Outra canção"))


def test_publicacoes_servicos_diferentes_confirmadas_reutilizam(client, logar):
    a, b = logar("plataforma_a"), logar("plataforma_b")
    r1 = client.post("/posts", headers=a, json={"selecao_externa": token(client, a), "nota": 8})
    r2 = client.post("/posts", headers=b, json={"selecao_externa": token(client, b, [faixa("deezer", "1")]), "nota": 8})
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["musica"]["id"] == r2.json()["musica"]["id"]
    assert contagem(ReferenciaExterna) == 2


def test_inconclusivos_geram_fila_somente_apos_publicacao(client, logar, monkeypatch):
    a, b = logar("revisao_a"), logar("revisao_b")
    f1, f2 = faixa(tipo_versao="desconhecida"), faixa("deezer", "1", tipo_versao="desconhecida")
    fonte(monkeypatch, [f1, f2])
    assert len(client.get("/musicas/busca?q=Canção", headers=a).json()["items"]) == 2
    assert contagem(RevisaoCorrespondencia) == 0
    for auth, f in [(a, f1), (b, f2)]:
        assert client.post("/posts", headers=auth, json={"selecao_externa": token(client, auth, [f]), "nota": 8}).status_code == 201
    assert contagem(RevisaoCorrespondencia) == 1


def test_busca_falhas_parciais_e_total_sem_perder_local(client, logar, monkeypatch):
    auth = logar("fontes")
    async def parcial(q):
        return [("spotify", "limite", []), ("deezer", "disponivel", [faixa("deezer", "1")])]
    monkeypatch.setattr(provedores_musicais, "buscar_fontes", parcial)
    resultado = client.get("/musicas/busca?q=Horizonte", headers=auth).json()
    assert resultado["fontes"]["spotify"] == "limite"
    assert resultado["items"][0]["fontes"] == ["local"]
    assert resultado["items"][-1]["fontes"] == ["deezer"]
    async def indisponiveis(q):
        return [("spotify", "indisponivel", []), ("deezer", "sem_acesso", [])]
    monkeypatch.setattr(provedores_musicais, "buscar_fontes", indisponiveis)
    assert client.get("/musicas/busca?q=Horizonte", headers=auth).json()["items"]
    assert client.get("/musicas/busca?q=a").status_code == 401


def test_sem_assinatura_preserva_busca_local(client, logar, monkeypatch):
    auth = logar("semchave")
    fonte(monkeypatch, [faixa()])
    monkeypatch.delenv("MUSICA_SELECTION_SECRET")
    resposta = client.get("/musicas/busca?q=Horizonte", headers=auth).json()
    assert resposta["fontes"]["spotify"] == "sem_assinatura"
    assert all(i["fontes"] == ["local"] for i in resposta["items"])


def test_pedido_autoria_validacao_aprovacao_sem_review(client, logar, id_da_musica):
    a, b = logar("pedido_a"), logar("pedido_b")
    dados = {"titulo": "Rara", "artista": "Artista", "justificativa": "Gravação independente"}
    assert client.post("/musicas/solicitacoes", headers=a, json={"titulo": "X", "artista": "Y"}).status_code == 422
    pedido = client.post("/musicas/solicitacoes", headers=a, json=dados).json()
    assert client.post("/musicas/solicitacoes", headers=a, json=dados).json()["id"] == pedido["id"]
    assert client.get("/musicas/solicitacoes", headers=b).json()["total"] == 0
    mid = id_da_musica(a)
    with SessionLocal() as db:
        op = Operacao(acao="aprovar", pedido_id=pedido["id"], musica_id=mid, motivo="Gravação já cadastrada")
        executar(db, [op], "Bruno")
        db.commit()
    estado = client.get("/musicas/solicitacoes", headers=a).json()["items"][0]
    assert estado["estado"] == "aprovado" and estado["musica_id"] == mid
    assert contagem(Post) == 0
    assert client.post("/posts", headers=a, json={"musica_id": mid, "nota": 8}).status_code == 201


def test_curadoria_previa_rollback_e_importacao_protegida(client, logar, id_da_musica):
    from app.services.musicas import importar_catalogo
    a = logar("curadoria")
    mid = id_da_musica(a)
    dados = dict(titulo="Título corrigido", artista="Artista", tipo_versao="original", generos=[" MPB ", "mpb"], tags=[])
    op = Operacao(acao="classificar", musica_id=mid, motivo="Revisão de Bruno", dados=dados)
    with SessionLocal() as db:
        executar(db, [op], "Bruno")
        db.rollback()
        assert db.get(Musica, mid).titulo != "Título corrigido"
        assert contagem(AuditoriaCatalogo) == 0
        executar(db, [op], "Bruno")
        db.commit()
        importar_catalogo(db)
        assert db.get(Musica, mid).titulo == "Título corrigido"
        assert db.get(Musica, mid).generos == ["mpb"]
    assert contagem(AuditoriaCatalogo) == 1


def test_lote_curadoria_invalido_reverte_tudo(client, logar, id_da_musica):
    a = logar("lote")
    mid = id_da_musica(a)
    with SessionLocal() as db:
        titulo = db.get(Musica, mid).titulo
        ops = [Operacao(acao="classificar", musica_id=mid, motivo="Corrigir", dados=dict(titulo="Novo", artista="A", tipo_versao="original")),
               Operacao(acao="recusar", pedido_id=9999, motivo="Não existe")]
        with pytest.raises(ValueError):
            executar(db, ops, "Bruno")
        db.rollback()
        assert db.get(Musica, mid).titulo == titulo
    assert contagem(AuditoriaCatalogo) == 0


def test_fusao_preserva_ids_reviews_e_bloqueia_conflitos(client, logar):
    from app.services.musicas import consultar
    a, b = logar("fusao_a"), logar("fusao_b")
    f1, f2 = faixa(tipo_versao="desconhecida"), faixa("deezer", "1", tipo_versao="desconhecida")
    p1 = client.post("/posts", headers=a, json={"selecao_externa": token(client, a, [f1]), "nota": 8}).json()
    p2 = client.post("/posts", headers=b, json={"selecao_externa": token(client, b, [f2]), "nota": 9}).json()
    m1, m2 = p1["musica"]["id"], p2["musica"]["id"]
    # Conflito: mesma pessoa publicou em ambas.
    extra = client.post("/posts", headers=a, json={"musica_id": m2, "nota": 8}).json()
    op = Operacao(acao="fundir", musica_id=m1, outra_musica_id=m2, motivo="Gravação confirmada")
    with SessionLocal() as db:
        with pytest.raises(ValueError, match="conflito"):
            executar(db, [op], "Bruno")
        db.rollback()
    client.delete(f"/posts/{extra['id']}", headers=a)
    with SessionLocal() as db:
        impactos = executar(db, [op], "Bruno")
        db.commit()
        assert impactos[0]["reviews_transferidas"] == 1
        assert db.get(Post, p2["id"]).musica_id == m1
        assert db.get(Musica, m2).incorporada_em == m1
        assert consultar(db, m2).id == m1
    assert contagem(Post) == 2


def test_normalizadores_oficiais_campos_opcionais():
    sp = provedores_musicais.Spotify.normalizar({"id": "abc", "name": "Faixa", "artists": [{"name": "A"}],
                                                "external_urls": {"spotify": "https://open.spotify.com/track/abc"}})
    assert sp.isrc == "" and sp.tipo_versao == "desconhecida"
    dz = provedores_musicais.Deezer.normalizar({"id": 1, "title": "Faixa", "artist": {"name": "A"},
                                               "duration": 180, "link": "https://www.deezer.com/track/1"})
    assert dz.duracao_ms == 180000


def test_fonte_timeout_e_rate_limit_nao_vazam_erros(monkeypatch):
    import asyncio
    class Falha:
        nome = "spotify"
        async def buscar(self, q):
            raise httpx.ConnectError("não expor detalhes")
    class Limite:
        nome = "deezer"
        async def buscar(self, q):
            raise provedores_musicais.FonteIndisponivel("limite")
    monkeypatch.setattr(provedores_musicais, "PROVEDORES", [Falha(), Limite()])
    assert asyncio.run(provedores_musicais.buscar_fontes("q")) == [("spotify", "indisponivel", []), ("deezer", "limite", [])]


def test_migracao_antiga_idempotente_preserva_ids(tmp_path, monkeypatch):
    from sqlalchemy import create_engine, text
    import app.db as modulo_db
    engine = create_engine(f"sqlite:///{tmp_path / 'antigo.db'}")
    with engine.begin() as db:
        db.execute(text("CREATE TABLE musicas(id INTEGER PRIMARY KEY, chave_catalogo TEXT, titulo TEXT)"))
        db.execute(text("INSERT INTO musicas VALUES(37, 'chave-estavel', 'Título')"))
    monkeypatch.setattr(modulo_db, "engine", engine)
    modulo_db.atualizar_esquema_antigo()
    modulo_db.atualizar_esquema_antigo()
    with engine.connect() as db:
        linha = db.execute(text("SELECT * FROM musicas")).mappings().one()
        assert linha["id"] == 37 and linha["chave_catalogo"] == "chave-estavel"
        assert linha["curadoria_estado"] == "curado" and linha["curadoria_protegida"] == 0
        assert linha["incorporada_em"] is None
    engine.dispose()


def test_cli_previa_aprovacao_auditoria_e_recusa(client, logar, tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    auth = logar("cli")
    pedido = client.post("/musicas/solicitacoes", headers=auth, json={
        "titulo": "Independente", "artista": "A", "referencia": "https://example.org/faixa"}).json()
    arquivo = tmp_path / "lote.json"
    arquivo.write_text(json.dumps([{"acao": "aprovar", "pedido_id": pedido["id"], "motivo": "Conferido",
                                   "dados": {"titulo": "Independente", "artista": "A", "tipo_versao": "desconhecida"}}]))
    comando = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/curadoria_catalogo.py"),
               "executar", "--arquivo", str(arquivo), "--autor", "Bruno"]
    previa = subprocess.run(comando, capture_output=True, text=True, env=os.environ.copy())
    assert previa.returncode == 0, previa.stderr
    assert json.loads(previa.stdout)["modo"] == "previa_revertida"
    assert contagem(AuditoriaCatalogo) == 0
    with SessionLocal() as db:
        assert db.get(SolicitacaoInclusao, pedido["id"]).estado == "pendente"
    aplicada = subprocess.run(comando + ["--aplicar"], capture_output=True, text=True, env=os.environ.copy())
    assert aplicada.returncode == 0, aplicada.stderr
    assert contagem(AuditoriaCatalogo) == 1 and contagem(Post) == 0
    pedido2 = client.post("/musicas/solicitacoes", headers=auth, json={
        "titulo": "Outra", "artista": "A", "justificativa": "Sem referência"}).json()
    with SessionLocal() as db:
        executar(db, [Operacao(acao="recusar", pedido_id=pedido2["id"], motivo="Falta identificar a gravação")], "Bruno")
        db.commit()
    estado = client.get("/musicas/solicitacoes", headers=auth).json()["items"][0]
    assert estado["estado"] == "recusado" and estado["motivo"] == "Falta identificar a gravação"


def test_adaptadores_http_usam_endpoints_oficiais(monkeypatch):
    import asyncio
    monkeypatch.setenv("SPOTIFY_BUSCA_VALIDADA", "true")
    monkeypatch.setenv("DEEZER_BUSCA_VALIDADA", "true")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "app_teste")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "segredo_teste")
    pedidos = []
    def handler(req):
        pedidos.append(req)
        if req.url.host == "accounts.spotify.com":
            assert req.method == "POST" and b"grant_type=client_credentials" in req.content
            return httpx.Response(200, json={"access_token": "token_teste", "expires_in": 3600})
        if req.url.host == "api.spotify.com":
            assert req.headers["Authorization"] == "Bearer token_teste"
            assert req.url.params["limit"] == "10" and req.url.params["market"] == "BR"
            return httpx.Response(200, json={"tracks": {"items": [{"id": "abc", "name": "Canção",
                "artists": [{"name": "A"}], "external_urls": {"spotify": "https://open.spotify.com/track/abc"}}]}})
        if req.url.path == "/search/track":
            return httpx.Response(200, json={"data": [{"id": 1}]})
        assert req.url.host == "api.deezer.com" and req.url.path == "/track/1"
        return httpx.Response(200, json={"id": 1, "title": "Canção", "artist": {"name": "A"},
            "contributors": [{"name": "A"}, {"name": "B"}], "isrc": "BRABC2600001", "duration": 180,
            "link": "https://www.deezer.com/track/1"})
    original = httpx.AsyncClient
    monkeypatch.setattr(provedores_musicais.httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    sp, dz = provedores_musicais.Spotify(), provedores_musicais.Deezer()
    async def buscar():
        return await asyncio.gather(sp.buscar("Canção"), dz.buscar("Canção"))
    resultados = asyncio.run(buscar())
    assert resultados[1][0].artistas == ["A", "B"]
    assert len(pedidos) == 4


def test_exemplos_do_contrato_de_dados():
    from pathlib import Path
    conteudo = json.loads((Path(__file__).resolve().parents[1] / "data/exemplos_correspondencia.json").read_text())
    for caso in conteudo["casos"]:
        a, b = FaixaExterna.model_validate(caso["a"]), FaixaExterna.model_validate(caso["b"])
        assert mesma_gravacao(a, b) is caso["mesma_gravacao"], caso["nome"]


def test_correspondencia_ambigua_publica_separada_para_revisao(client, logar):
    auth = logar("ambigua")
    with SessionLocal() as db:
        for numero in (1, 2):
            m = Musica(chave_catalogo=f"ambigua-{numero}", titulo="Canção - Original Version", artista="Artista",
                       tipo_versao="original", descricao_versao="Original Version", generos=[], tags=[], capa_url="")
            db.add(m)
            db.flush()
            f = faixa("deezer", str(numero))
            db.add(ReferenciaExterna(musica_id=m.id, servico=f.servico, id_externo=f.id_externo,
                                     metadados=f.model_dump(mode="json"), isrc=f.isrc))
        db.commit()
    antes = contagem(Musica)
    resposta = client.post("/posts", headers=auth, json={"selecao_externa": token(client, auth), "nota": 8})
    assert resposta.status_code == 201, resposta.text
    assert contagem(Musica) == antes + 1
    assert contagem(RevisaoCorrespondencia) == 2
