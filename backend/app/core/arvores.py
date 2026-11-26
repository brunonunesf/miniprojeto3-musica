"""Floresta de reviews em memória; sem dependências de banco ou servidor."""
from collections import deque
from dataclasses import dataclass, replace
from typing import Iterable, Literal

Identificador = int | str


class ErroArvore(ValueError):
    """Base dos erros de contrato da estrutura."""


class NoInexistente(ErroArvore):
    pass


class EstruturaInvalida(ErroArvore):
    pass


class ParametroInvalido(ErroArvore):
    pass


def _validar_id(valor: Identificador) -> None:
    if type(valor) not in (int, str):
        raise ParametroInvalido('Identificador deve ser int ou str, sem conversão')


@dataclass(frozen=True, slots=True)
class RegistroReview:
    review_id: Identificador
    musica_id: Identificador
    autor_id: Identificador
    origem_id: Identificador | None = None
    apagada: bool = False

    def __post_init__(self) -> None:
        for valor in (self.review_id, self.musica_id, self.autor_id):
            _validar_id(valor)
        if self.origem_id is not None:
            _validar_id(self.origem_id)
        if type(self.apagada) is not bool:
            raise ParametroInvalido('apagada deve ser bool')


@dataclass(frozen=True, slots=True)
class Passo:
    no: RegistroReview
    distancia: int


@dataclass(frozen=True, slots=True)
class Pagina:
    itens: tuple[Passo, ...]
    tem_mais: bool


class FlorestaReviews:
    def __init__(self) -> None:
        self._nos: dict[Identificador, RegistroReview] = {}
        self._filhos: dict[Identificador, list[Identificador]] = {}
        self._raizes: dict[Identificador, list[Identificador]] = {}

    def reconstruir(self, registros: Iterable[RegistroReview]) -> None:
        """Carga atômica O(n), inclusive com filhos antes de seus pais."""
        nova = FlorestaReviews()
        for no in registros:
            if not isinstance(no, RegistroReview):
                raise ParametroInvalido('Esperado RegistroReview')
            if no.review_id in nova._nos:
                raise EstruturaInvalida(f'ID duplicado: {no.review_id!r}')
            nova._nos[no.review_id] = no
            nova._filhos[no.review_id] = []
        for no in nova._nos.values():
            if no.origem_id is None:
                nova._raizes.setdefault(no.musica_id, []).append(no.review_id)
            else:
                pai = nova._nos.get(no.origem_id)
                if pai is None:
                    raise EstruturaInvalida(f'Origem ausente: {no.origem_id!r}')
                if pai.musica_id != no.musica_id:
                    raise EstruturaInvalida('Origem de outra música')
                nova._filhos[pai.review_id].append(no.review_id)
        # Cada nó entra em um único caminho; não refazer a subida para cada nó.
        concluidos: set[Identificador] = set()
        for inicio in nova._nos:
            caminho: set[Identificador] = set()
            atual: Identificador | None = inicio
            while atual is not None and atual not in concluidos:
                if atual in caminho:
                    raise EstruturaInvalida(f'Ciclo envolvendo {atual!r}')
                caminho.add(atual)
                atual = nova._nos[atual].origem_id
            concluidos.update(caminho)
        self._nos, self._filhos, self._raizes = nova._nos, nova._filhos, nova._raizes

    def inserir(self, no: RegistroReview) -> None:
        """Insere ID novo em O(1) esperado; nunca muda o pai de um nó existente."""
        if not isinstance(no, RegistroReview):
            raise ParametroInvalido('Esperado RegistroReview')
        if no.review_id in self._nos:
            raise EstruturaInvalida(f'ID duplicado: {no.review_id!r}')
        if no.origem_id is not None:
            pai = self._nos.get(no.origem_id)
            if pai is None or pai.apagada or pai.musica_id != no.musica_id:
                raise EstruturaInvalida('Origem deve existir, estar ativa e ser da mesma música')
        self._nos[no.review_id] = no
        self._filhos[no.review_id] = []
        if no.origem_id is None:
            self._raizes.setdefault(no.musica_id, []).append(no.review_id)
        else:
            self._filhos[no.origem_id].append(no.review_id)

    def consultar(self, review_id: Identificador) -> RegistroReview:
        _validar_id(review_id)
        try:
            return self._nos[review_id]
        except KeyError:
            raise NoInexistente(f'Review inexistente: {review_id!r}') from None

    def marcar_apagada(self, review_id: Identificador) -> RegistroReview:
        no = self.consultar(review_id)
        apagada = replace(no, apagada=True)
        self._nos[review_id] = apagada
        return apagada

    def pai(self, review_id: Identificador) -> RegistroReview | None:
        origem = self.consultar(review_id).origem_id
        return None if origem is None else self.consultar(origem)

    def raiz(self, review_id: Identificador) -> RegistroReview:
        no = self.consultar(review_id)
        while no.origem_id is not None:
            no = self._nos[no.origem_id]
        return no

    def raizes(self, musica_id: Identificador) -> tuple[RegistroReview, ...]:
        _validar_id(musica_id)
        return tuple(self._nos[i] for i in self._raizes.get(musica_id, ()))

    @staticmethod
    def _limites(offset: int, limit: int, profundidade_maxima: int | None) -> None:
        if type(offset) is not int or offset < 0:
            raise ParametroInvalido('offset deve ser inteiro não negativo')
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ParametroInvalido('limit deve estar entre 1 e 200')
        if profundidade_maxima is not None and (
            type(profundidade_maxima) is not int or profundidade_maxima < 0
        ):
            raise ParametroInvalido('profundidade_maxima deve ser inteiro não negativo ou None')

    @staticmethod
    def _paginar(passos: Iterable[Passo], offset: int, limit: int) -> Pagina:
        itens: list[Passo] = []
        for indice, passo in enumerate(passos):
            if indice < offset:
                continue
            if len(itens) == limit:
                return Pagina(tuple(itens), True)
            itens.append(passo)
        return Pagina(tuple(itens), False)

    def ancestrais(self, review_id: Identificador, *, offset: int = 0,
                   limit: int = 50, profundidade_maxima: int | None = None) -> Pagina:
        self._limites(offset, limit, profundidade_maxima)
        no = self.consultar(review_id)

        def passos():
            origem = no.origem_id
            distancia = 1
            while origem is not None and (profundidade_maxima is None or distancia <= profundidade_maxima):
                ancestral = self._nos[origem]
                yield Passo(ancestral, distancia)
                origem = ancestral.origem_id
                distancia += 1

        return self._paginar(passos(), offset, limit)

    def descendentes(self, review_id: Identificador, *, ordem: Literal['bfs', 'dfs'] = 'bfs',
                     offset: int = 0, limit: int = 50,
                     profundidade_maxima: int | None = None) -> Pagina:
        self._limites(offset, limit, profundidade_maxima)
        if ordem not in ('bfs', 'dfs'):
            raise ParametroInvalido('ordem deve ser bfs ou dfs')
        self.consultar(review_id)

        def passos():
            pendentes = deque([(review_id, 0)])
            while pendentes:
                atual, distancia = pendentes.popleft() if ordem == 'bfs' else pendentes.pop()
                if distancia:
                    yield Passo(self._nos[atual], distancia)
                if profundidade_maxima is None or distancia < profundidade_maxima:
                    filhos = self._filhos[atual]
                    sequencia = filhos if ordem == 'bfs' else reversed(filhos)
                    pendentes.extend((filho, distancia + 1) for filho in sequencia)

        return self._paginar(passos(), offset, limit)


arvores_reviews = FlorestaReviews()
