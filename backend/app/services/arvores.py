from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.arvores import NoInexistente, RegistroReview
from app.core.floresta import floresta
from app.models.musica import Musica
from app.models.post import Post
from app.models.review_apagada import ReviewApagada
from app.schemas.arvore import ArvoreOut, AutorDoNo, NoArvore

# Quantas reviews uma leitura da árvore devolve, no máximo, além da raiz. Se a árvore tem mais do que
# isso, `truncada` fica verdadeiro.
LIMITE_DA_ARVORE = 200


def reconstruir(db: Session) -> None:
    """Refaz a floresta em memória a partir do banco: reviews existentes e reviews apagadas."""
    ativas = db.execute(select(Post.id, Post.musica_id, Post.autor_id, Post.origem_id)).all()
    apagadas = db.execute(
        select(ReviewApagada.id, ReviewApagada.musica_id, ReviewApagada.autor_id, ReviewApagada.origem_id)
    ).all()
    registros = [RegistroReview(i, m, a, o) for i, m, a, o in ativas]
    registros += [RegistroReview(i, m, a, o, apagada=True) for i, m, a, o in apagadas]
    floresta.reconstruir(sorted(registros, key=lambda r: r.review_id))


def ler(db: Session, post_id: int) -> ArvoreOut:
    """A árvore em que a review está: a raiz e todos os ramos, em ordem de publicação por nível.

    Custo: subir até a raiz é O(profundidade). O limite restringe a saída, mas
    o BFS pode enfileirar todos os filhos de um nó largo: tempo e memória O(n)
    no pior caso, conforme o contrato da #41. A leitura usa a floresta em memória e uma consulta ao banco para os dados
    das reviews que ainda existem.
    """
    try:
        raiz = floresta.raiz(post_id)
    except NoInexistente:
        # A floresta pode estar atrás do banco (dados gravados por fora da API, como um seed).
        # Se a review existe no banco, ela é refeita e a leitura tenta de novo; senão, é 404.
        if db.get(Post, post_id) is None and db.get(ReviewApagada, post_id) is None:
            raise HTTPException(status_code=404, detail="review não encontrada")
        reconstruir(db)
        raiz = floresta.raiz(post_id)

    pagina = floresta.descendentes(raiz.review_id, ordem="bfs", limit=LIMITE_DA_ARVORE)
    registros = [raiz] + [passo.no for passo in pagina.itens]

    ids_ativos = [r.review_id for r in registros if not r.apagada]
    reviews = {
        p.id: p
        for p in db.scalars(select(Post).where(Post.id.in_(ids_ativos)).options(selectinload(Post.autor)))
    }

    nos: dict[int, NoArvore] = {}
    for registro in registros:  # em largura: o pai sempre vem antes dos filhos
        review = reviews.get(registro.review_id)
        no = NoArvore(
            id=registro.review_id,
            apagada=registro.apagada,
            autor=AutorDoNo(username=review.autor.username, name=review.autor.name) if review else None,
            nota=review.nota if review else None,
            filhos=[],
        )
        nos[registro.review_id] = no
        if registro.origem_id in nos:
            nos[registro.origem_id].filhos.append(no)

    return ArvoreOut(
        musica=db.get(Musica, raiz.musica_id),
        raiz=nos[raiz.review_id],
        truncada=pagina.tem_mais,
    )
