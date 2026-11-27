"""Motor puro: snapshots atuais, TF-IDF de metadados e cosseno."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


class EntradaInvalida(ValueError):
    """Snapshot inconsistente."""


@dataclass(frozen=True)
class Musica:
    chave: str
    artista: str
    generos: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Review:
    id: int
    musica: str
    autor: int
    data: datetime
    publica: bool = True
    ativa: bool = True


@dataclass(frozen=True)
class Curtida:
    usuario: int
    review: int


@dataclass(frozen=True)
class Sugestao:
    musica: str
    review_id: int
    similaridade: float
    motivo: str
    caracteristicas: tuple[str, ...]


def _normalizar(valor):
    return ' '.join(valor.split()).casefold()


def _id(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def _termos(m):
    return tuple(sorted({f'{campo}:{_normalizar(v)}'
                         for campo, valores in [('artista', (m.artista,)),
                                                ('genero', m.generos), ('tag', m.tags)]
                         for v in valores if _normalizar(v)}))


def _analisar(termos):
    return termos


class Recomendador:
    """Construa nova instância após mudar catálogo; perfis não são armazenados.

    Recebe reviews e curtidas de um snapshot autorizado pelo backend. Somente
    as interações do usuário solicitado formam o perfil. Retorna todo o ranking,
    para paginação posterior na API. Datas precisam incluir fuso horário.
    """

    def __init__(self, catalogo: Iterable[Musica]):
        musicas = list(catalogo)
        if any(not isinstance(m.chave, str) or not m.chave.strip() for m in musicas):
            raise EntradaInvalida('Chave de catálogo vazia')
        if len({m.chave for m in musicas}) != len(musicas):
            raise EntradaInvalida('Chave de catálogo duplicada')
        self._musicas = tuple(sorted(musicas, key=lambda m: m.chave))
        self._pos = {m.chave: i for i, m in enumerate(self._musicas)}
        documentos = [_termos(m) for m in self._musicas]
        self._nomes = ()
        self._matriz = csr_matrix((len(musicas), 0), dtype=float)
        if any(documentos):
            vetorizador = TfidfVectorizer(analyzer=_analisar, binary=True,
                                         use_idf=True, smooth_idf=True,
                                         sublinear_tf=False, norm='l2')
            self._matriz = vetorizador.fit_transform(documentos)
            self._nomes = tuple(vetorizador.get_feature_names_out())

    def recomendar(self, usuario: int, reviews: Iterable[Review],
                   curtidas: Iterable[Curtida]) -> tuple[Sugestao, ...]:
        if not _id(usuario):
            raise EntradaInvalida('Usuário deve ser inteiro positivo')
        registros = {}
        for r in reviews:
            if (not _id(r.id) or not _id(r.autor) or r.musica not in self._pos
                    or not isinstance(r.data, datetime) or r.data.tzinfo is None
                    or r.data.utcoffset() is None
                    or not isinstance(r.publica, bool) or not isinstance(r.ativa, bool)):
                raise EntradaInvalida('Review com referência, identidade ou data inválida')
            if r.id in registros and registros[r.id] != r:
                raise EntradaInvalida('Review duplicada conflitante')
            registros[r.id] = r
        pares = set()
        for c in curtidas:
            if not _id(c.usuario) or not _id(c.review) or c.review not in registros:
                raise EntradaInvalida('Curtida com referência ou identidade inválida')
            pares.add((c.usuario, c.review))
        elegiveis = {i: r for i, r in registros.items() if r.ativa and r.publica}
        contagens = defaultdict(int)
        pesos = {}
        for u, rid in sorted(pares):
            if rid not in elegiveis:
                continue
            r = elegiveis[rid]
            contagens[rid] += 1
            if u == usuario and r.autor != usuario:
                pesos[r.musica] = 1
        analisadas = {r.musica for r in registros.values() if r.ativa and r.autor == usuario}
        pesos.update({chave: 3 for chave in analisadas})
        perfil = csr_matrix((1, self._matriz.shape[1]), dtype=float)
        for chave in sorted(pesos):
            perfil = perfil + self._matriz[self._pos[chave]] * pesos[chave]
        tem_perfil = bool(perfil.nnz)
        if tem_perfil:
            perfil = normalize(perfil, norm='l2')
        representantes = {}
        def ordem_review(r):
            return (contagens[r.id], r.data.timestamp(), r.id)
        for r in elegiveis.values():
            if r.musica in analisadas:
                continue
            anterior = representantes.get(r.musica)
            if anterior is None or ordem_review(r) > ordem_review(anterior):
                representantes[r.musica] = r
        positivas, fallback = [], []
        for chave, r in representantes.items():
            contribuicoes = self._matriz[self._pos[chave]].multiply(perfil).tocsr()
            score = float(contribuicoes.sum())
            termos = tuple(self._nomes[i] for i, v in sorted(
                zip(contribuicoes.indices, contribuicoes.data),
                key=lambda par: (-par[1], self._nomes[par[0]]))[:3] if v > 0)
            s = Sugestao(chave, r.id, score, 'afinidade' if score > 0 else
                         ('sem_afinidade' if tem_perfil else 'sem_sinais'), termos)
            ordem = (-r.data.timestamp(), chave)
            if score > 0:
                positivas.append(((-score, *ordem), s))
            else:
                fallback.append((ordem, s))
        resultado = [s for _, s in sorted(positivas)]
        grupos = {}
        for _, s in sorted(fallback):
            artista = _normalizar(self._musicas[self._pos[s.musica]].artista)
            grupos.setdefault(artista, []).append(s)
        rodada = 0
        while grupos:
            restantes = {}
            for artista, itens in grupos.items():
                resultado.append(itens[rodada])
                if len(itens) > rodada + 1:
                    restantes[artista] = itens
            grupos = restantes
            rodada += 1
        return tuple(resultado)
