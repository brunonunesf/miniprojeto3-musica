from itertools import zip_longest
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.catalogo_externo import ReferenciaExterna, RevisaoCorrespondencia, SolicitacaoInclusao
from app.models.musica import Musica
from app.schemas.catalogo_externo import FaixaExterna, SolicitacaoCreate
from app.schemas.musica import MusicaOut
from app.services import musicas, provedores_musicais, selecao_musical
from app.services.identidade_musical import mesma_gravacao, normalizar


def referencia(db, f):
    return db.scalar(select(ReferenciaExterna).where(ReferenciaExterna.servico == f.servico,
                                                    ReferenciaExterna.id_externo == f.id_externo))


def candidatas(db, f):
    return list(db.scalars(select(ReferenciaExterna).where(ReferenciaExterna.isrc == f.isrc))) if f.isrc else []


def identidade_conhecida(db, faixas):
    ids = {musica_canonica_id(db, ref.musica_id) for f in faixas if (ref := referencia(db, f)) is not None}
    return ids


def musica_canonica_id(db, identificador):
    return musicas.consultar(db, identificador).id


async def buscar(db: Session, q: str, usuario_id: int):
    locais, total_local = musicas.listar(db, q, 0, 20)
    fontes = await provedores_musicais.buscar_fontes(q) if q.strip() else [
        (p.nome, "aguardando_busca", []) for p in provedores_musicais.PROVEDORES]
    # Sem chave compartilhada não emite seleções que falhariam em outro worker.
    grupos: list[list[FaixaExterna]] = []
    for linha in zip_longest(*(f[2] for f in fontes)):
        for faixa in linha:
            if faixa is None:
                continue
            for grupo in grupos:
                ids_grupo = identidade_conhecida(db, grupo)
                ids_faixa = identidade_conhecida(db, [faixa])
                conhecida = bool(ids_grupo and ids_grupo == ids_faixa)
                # Nunca agrupa duas identidades já persistidas diferentes sem curadoria.
                if conhecida or (len(ids_grupo | ids_faixa) <= 1 and all(mesma_gravacao(faixa, g) for g in grupo)):
                    grupo.append(faixa)
                    break
            else:
                grupos.append([faixa])
    items = [{"chave": f"local:{m.id}", "musica_id": m.id, "selecao_externa": None,
              "musica": MusicaOut.model_validate(m).model_dump(), "fontes": ["local"], "referencias": []}
             for m in locais]
    for grupo in grupos:
        ids = identidade_conhecida(db, grupo)
        if not ids:
            # Pode corresponder a vínculo de outro serviço já persistido.
            ids = {r.musica_id for f in grupo for r in candidatas(db, f)
                   if mesma_gravacao(f, FaixaExterna.model_validate(r.metadados))}
        identificador = next(iter(ids)) if len(ids) == 1 else None
        f = grupo[0]
        try:
            token = selecao_musical.assinar(grupo, usuario_id)
        except HTTPException:
            fontes = [(nome, "sem_assinatura" if estado == "disponivel" else estado, faixas)
                      for nome, estado, faixas in fontes]
            continue
        existente = next((i for i in items if identificador and i["musica_id"] == identificador), None)
        if existente:
            # A seleção assinada também associa novos vínculos no momento da publicação.
            existente["selecao_externa"] = token
            existente["fontes"] = list(dict.fromkeys(existente["fontes"] + [x.servico for x in grupo]))
            existente["referencias"].extend({"servico": x.servico, "url": str(x.url)} for x in grupo)
            continue
        m = musicas.consultar(db, identificador) if identificador else None
        items.append({"chave": f"{f.servico}:{f.id_externo}", "musica_id": identificador,
                      "selecao_externa": token, "fontes": list(dict.fromkeys(x.servico for x in grupo)),
                      "referencias": [{"servico": x.servico, "url": str(x.url)} for x in grupo],
                      "musica": MusicaOut.model_validate(m).model_dump() if m else {
                          "album": f.album, "duracao_ms": f.duracao_ms, "titulo": f.titulo, "artista": ", ".join(f.artistas), "tipo_versao": f.tipo_versao,
                          "descricao_versao": f.descricao_versao, "capa_url": str(f.capa_url or ""),
                          "generos": [], "tags": []}})
    return {"items": items, "total_local": total_local,
            "fontes": {"local": "disponivel", **{nome: estado for nome, estado, _ in fontes}}}


def travar_escrita(db: Session):
    # SQLite: adquire a trava de escrita ANTES de ler identidades; vale entre processos.
    # UPDATE sem linhas não altera dados e evita o race read-then-insert.
    db.execute(update(Musica).where(Musica.id == -1).values(id=-1))


def resolver(db: Session, faixas: list[FaixaExterna]) -> Musica:
    ids = identidade_conhecida(db, faixas)
    if len(ids) > 1:
        raise HTTPException(409, "Correspondência mudou. Busque novamente; a curadoria precisa revisar as identidades.")
    if not ids:
        ids = {r.musica_id for f in faixas for r in candidatas(db, f)
               if mesma_gravacao(f, FaixaExterna.model_validate(r.metadados))}
    if len(ids) > 1:
        # Mais de uma candidata não confirma identidade: cria separada e encaminha à fila.
        ids = set()
    if ids:
        musica = musicas.consultar(db, next(iter(ids)))
    else:
        f = faixas[0]
        musica = Musica(chave_catalogo=f"externa-{uuid4().hex}", titulo=f.titulo, artista=", ".join(f.artistas),
                        tipo_versao=f.tipo_versao, descricao_versao=f.descricao_versao,
                        generos=[], tags=[], capa_url=str(f.capa_url or ""), curadoria_estado="pendente")
        db.add(musica)
        db.flush()
    for f in faixas:
        if referencia(db, f) is None:
            db.add(ReferenciaExterna(musica_id=musica.id, servico=f.servico, id_externo=f.id_externo,
                                     metadados=f.model_dump(mode="json"), isrc=f.isrc))
    db.flush()
    # Fila somente após seleção publicada, nunca por resultado de busca.
    similares = list(db.scalars(select(Musica).where(Musica.id != musica.id, Musica.incorporada_em.is_(None))))
    referencias = list(db.scalars(select(ReferenciaExterna).where(ReferenciaExterna.musica_id != musica.id)))
    suspeitas = {m.id for m in similares if normalizar(m.titulo) == normalizar(musica.titulo)
                 and normalizar(m.artista) == normalizar(musica.artista)}
    suspeitas |= {r.musica_id for r in referencias if r.isrc and any(r.isrc == f.isrc for f in faixas)}
    for outro in suspeitas:
        a, b = sorted((musica.id, outro))
        existe = db.scalar(select(RevisaoCorrespondencia).where(
            RevisaoCorrespondencia.musica_a == a, RevisaoCorrespondencia.musica_b == b))
        if not existe:
            db.add(RevisaoCorrespondencia(musica_a=a, musica_b=b))
    return musica


def solicitar(db, usuario_id: int, dados: SolicitacaoCreate):
    repetida = db.scalar(select(SolicitacaoInclusao).where(
        SolicitacaoInclusao.usuario_id == usuario_id, SolicitacaoInclusao.estado == "pendente",
        SolicitacaoInclusao.titulo == dados.titulo, SolicitacaoInclusao.artista == dados.artista,
        SolicitacaoInclusao.versao == dados.versao))
    if repetida:
        return repetida
    pedido = SolicitacaoInclusao(usuario_id=usuario_id, **dados.model_dump())
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido
