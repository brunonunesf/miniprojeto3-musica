"""Bibliotecas pessoais e privacidade (issue #12).

Cada pessoa tem duas listas, calculadas a partir das reviews dela: as **descobertas** (músicas que conheceu por
outra review, ou seja, as derivadas) e as **recomendações** (as que indicou por conta própria, as independentes).
Como saem das reviews vivas, ficam coerentes sozinhas: apagar uma review a tira da lista, corrigir a origem muda a
origem mostrada, e curtir, visitar ou comentar não registram nada. Uma música aparece uma vez só, porque há uma
review ativa por pessoa e música. Só a visibilidade é guardada, numa linha que só existe depois da primeira mudança.
"""

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User
from app.models.visibilidade_biblioteca import VisibilidadeBiblioteca
from app.schemas.biblioteca import BibliotecaOut, BibliotecaPage, BibliotecaUpdate, ListaResumo
from app.services import posts, users

LISTAS = ("descobertas", "recomendacoes")


def _publicas(db: Session, dono_id: int) -> dict[str, bool]:
    """Sem linha valem os padrões: descobertas privadas e recomendações públicas."""
    linha = db.get(VisibilidadeBiblioteca, dono_id)
    if linha is None:
        return {"descobertas": False, "recomendacoes": True}
    return {"descobertas": linha.descobertas_publicas, "recomendacoes": linha.recomendacoes_publicas}


def _filtro(lista: str, dono_id: int):
    de_quem = Post.autor_id == dono_id
    return and_(de_quem, Post.origem_id.is_not(None) if lista == "descobertas" else Post.origem_id.is_(None))


def _rotulo(publica: bool) -> str:
    return "publica" if publica else "privada"


def _resumo_da_lista(db: Session, quem_pede: User, dono: User, lista: str, publicas: dict[str, bool]) -> ListaResumo:
    acessivel = quem_pede.id == dono.id or publicas[lista]
    total = None
    if acessivel:
        total = db.scalar(select(func.count()).select_from(Post).where(_filtro(lista, dono.id))) or 0
    return ListaResumo(visibilidade=_rotulo(publicas[lista]), acessivel=acessivel, total=total)


def resumo(db: Session, quem_pede: User, username: str) -> BibliotecaOut:
    """As duas listas de uma pessoa (404 se ela não existe): a dona vê tudo, os outros só o que é público."""
    dono = users.buscar_por_username(db, username)
    publicas = _publicas(db, dono.id)
    return BibliotecaOut(**{lista: _resumo_da_lista(db, quem_pede, dono, lista, publicas) for lista in LISTAS})


def listar(db: Session, quem_pede: User, username: str, lista: str, offset: int, limit: int) -> BibliotecaPage:
    """Uma página de uma lista, da mais nova para a mais antiga.

    Lista inexistente é 404. Lista restrita a quem pede é 403, **mesmo vazia**: assim ninguém descobre, pela
    resposta, se a lista tem itens, quantos são nem de onde vieram.
    """
    if lista not in LISTAS:
        raise HTTPException(status_code=404, detail="lista de biblioteca não encontrada")
    dono = users.buscar_por_username(db, username)
    publicas = _publicas(db, dono.id)
    if quem_pede.id != dono.id and not publicas[lista]:
        raise HTTPException(status_code=403, detail="esta lista é privada")
    reviews, total = posts.listar_reviews(db, quem_pede, _filtro(lista, dono.id), offset, limit)
    return BibliotecaPage(
        lista=lista, visibilidade=_rotulo(publicas[lista]), items=reviews, total=total, offset=offset, limit=limit
    )


def atualizar(db: Session, user: User, dados: BibliotecaUpdate) -> BibliotecaOut:
    """Muda a visibilidade das listas de quem está logado. Repetir o mesmo valor não muda nada."""
    for _ in range(2):
        linha = db.get(VisibilidadeBiblioteca, user.id)
        if linha is None:
            linha = VisibilidadeBiblioteca(usuario_id=user.id)
            db.add(linha)
        if dados.descobertas is not None:
            linha.descobertas_publicas = dados.descobertas == "publica"
        if dados.recomendacoes is not None:
            linha.recomendacoes_publicas = dados.recomendacoes == "publica"
        try:
            db.commit()
            break
        except IntegrityError:
            # duas requisições criaram a linha da mesma pessoa ao mesmo tempo: a segunda tentativa a encontra
            db.rollback()
    else:
        raise HTTPException(status_code=409, detail="não foi possível salvar agora; tente de novo")
    return resumo(db, user, user.username)
