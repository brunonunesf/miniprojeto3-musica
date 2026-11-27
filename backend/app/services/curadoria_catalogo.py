"""Operações administrativas: o chamador decide commit ou rollback da prévia."""
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, update

from app.models.catalogo_externo import AuditoriaCatalogo, ReferenciaExterna, RevisaoCorrespondencia, SolicitacaoInclusao
from app.models.musica import Musica
from app.models.post import Post
from app.models.review_apagada import ReviewApagada
from app.schemas.catalogo_externo import FaixaExterna, Versao
from app.services.catalogo_externo import referencia, travar_escrita
from app.services.identidade_musical import normalizar
from app.services.musicas import consultar


class DadosCuradoria(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=200)
    artista: str = Field(min_length=1, max_length=200)
    tipo_versao: Versao
    descricao_versao: str = Field(default="", max_length=200)
    generos: list[str] = Field(default_factory=list, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=100)
    capa_url: str = Field(default="", max_length=2048)
    referencias: list[FaixaExterna] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def normalizar_dados(self):
        for campo in ("generos", "tags"):
            valores = getattr(self, campo)
            if any(not x.strip() or len(x) > 100 for x in valores):
                raise ValueError("gênero/tag inválido")
            setattr(self, campo, list(dict.fromkeys(normalizar(x) for x in valores)))
        if self.capa_url:
            from pydantic import HttpUrl, TypeAdapter
            TypeAdapter(HttpUrl).validate_python(self.capa_url)
        return self


class Operacao(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    acao: Literal["classificar", "aprovar", "recusar", "vincular", "fundir", "separar"]
    musica_id: int | None = Field(default=None, gt=0)
    pedido_id: int | None = Field(default=None, gt=0)
    outra_musica_id: int | None = Field(default=None, gt=0)
    dados: DadosCuradoria | None = None
    referencia: FaixaExterna | None = None
    motivo: str = Field(min_length=1, max_length=1000)


def exigir(valor, mensagem):
    if valor is None:
        raise ValueError(mensagem)
    return valor


def aplicar_dados(musica, dados):
    for campo, valor in dados.model_dump(exclude={"referencias"}).items():
        setattr(musica, campo, valor)
    musica.curadoria_estado = "curado"
    musica.curadoria_protegida = True


def vincular(db, musica, faixa):
    ref = referencia(db, faixa)
    if ref and consultar(db, ref.musica_id).id != musica.id:
        raise ValueError("referência já pertence a outra música; use fundir após revisar os impactos")
    if not ref:
        db.add(ReferenciaExterna(musica_id=musica.id, servico=faixa.servico, id_externo=faixa.id_externo,
                                 metadados=faixa.model_dump(mode="json"), isrc=faixa.isrc))


def fundir(db, destino, origem):
    if destino.id == origem.id:
        raise ValueError("selecione identidades diferentes")
    # Não apaga reviews nem resolve silenciosamente conflito de autoria.
    autores_destino = set(db.scalars(select(Post.autor_id).where(Post.musica_id == destino.id)))
    conflitos = list(db.scalars(select(Post.id).where(Post.musica_id == origem.id, Post.autor_id.in_(autores_destino))))
    if conflitos:
        raise ValueError(f"conflito de reviews da mesma pessoa: {conflitos}; resolva antes de fundir")
    quantidade = len(list(db.scalars(select(Post.id).where(Post.musica_id == origem.id))))
    for modelo, coluna in ((Post, Post.musica_id), (ReviewApagada, ReviewApagada.musica_id),
                           (ReferenciaExterna, ReferenciaExterna.musica_id), (SolicitacaoInclusao, SolicitacaoInclusao.musica_id)):
        db.execute(update(modelo).where(coluna == origem.id).values(musica_id=destino.id))
    db.execute(update(Musica).where(Musica.incorporada_em == origem.id).values(incorporada_em=destino.id))
    origem.incorporada_em = destino.id  # mantém o ID e a chave antiga como alias
    origem.curadoria_protegida = True
    revisoes = db.scalars(select(RevisaoCorrespondencia).where(
        (RevisaoCorrespondencia.musica_a == origem.id) | (RevisaoCorrespondencia.musica_b == origem.id)))
    for revisao in revisoes:
        revisao.estado = "resolvido"
    return quantidade


def executar(db, operacoes: list[Operacao], autor: str):
    if not autor.strip() or len(autor) > 100:
        raise ValueError("informe o autor da curadoria (até 100 caracteres)")
    travar_escrita(db)
    impactos = []
    for op in operacoes:
        musica = consultar(db, op.musica_id) if op.musica_id else None
        impacto = {"acao": op.acao}
        if op.acao in ("aprovar", "recusar"):
            pedido = db.get(SolicitacaoInclusao, exigir(op.pedido_id, "informe pedido_id"))
            if not pedido or pedido.estado != "pendente":
                raise ValueError("solicitação não existe ou já foi analisada")
            if op.acao == "recusar":
                pedido.estado = "recusado"
            else:
                if not musica:
                    dados = exigir(op.dados, "informe dados ou musica_id para aprovar")
                    musica = Musica(chave_catalogo=f"curadoria-{uuid4().hex}")
                    aplicar_dados(musica, dados)
                    db.add(musica)
                    db.flush()
                pedido.estado, pedido.musica_id = "aprovado", musica.id
            pedido.motivo = op.motivo
            impacto["pedido_id"] = pedido.id
        elif op.acao == "classificar":
            aplicar_dados(exigir(musica, "informe musica_id"), exigir(op.dados, "informe dados"))
        elif op.acao == "vincular":
            vincular(db, exigir(musica, "informe musica_id"), exigir(op.referencia, "informe referencia"))
        else:
            destino = exigir(musica, "informe musica_id (destino)")
            origem = consultar(db, exigir(op.outra_musica_id, "informe outra_musica_id"))
            if op.acao == "fundir":
                impacto["reviews_transferidas"] = fundir(db, destino, origem)
            else:
                a, b = sorted((destino.id, origem.id))
                if a == b:
                    raise ValueError("selecione identidades diferentes")
                revisao = db.scalar(select(RevisaoCorrespondencia).where(
                    RevisaoCorrespondencia.musica_a == a, RevisaoCorrespondencia.musica_b == b))
                if not revisao:
                    raise ValueError("par não está na fila de revisão")
                revisao.estado = "distintos"
        if musica and op.dados:
            for faixa in op.dados.referencias:
                vincular(db, musica, faixa)
        if musica:
            impacto["musica_id"] = musica.id
            impacto["titulo"] = musica.titulo
        db.add(AuditoriaCatalogo(autor=autor.strip(), motivo=op.motivo, acao=op.acao,
                                dados={"operacao": op.model_dump(mode="json"), "impacto": impacto}))
        db.flush()
        impactos.append(impacto)
    return impactos
