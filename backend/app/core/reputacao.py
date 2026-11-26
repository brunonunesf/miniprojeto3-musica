"""Motor puro de reputação; banco, permissões e sincronização ficam no service."""
from dataclasses import dataclass
from typing import Iterable
from app.core.arvores import FlorestaReviews, Identificador


class ErroReputacao(ValueError):
    """Entrada fora do contrato de reputação."""


def _validar_id(valor: Identificador) -> None:
    if type(valor) not in (int, str):
        raise ErroReputacao('Identificador deve ser int ou str, sem conversão')


@dataclass(frozen=True, slots=True)
class EventoCurtida:
    review_id: Identificador
    usuario_id: Identificador

    def __post_init__(self) -> None:
        _validar_id(self.review_id)
        _validar_id(self.usuario_id)


@dataclass(frozen=True, slots=True)
class EventoDerivada:
    review_id: Identificador

    def __post_init__(self) -> None:
        _validar_id(self.review_id)


Evento = EventoCurtida | EventoDerivada
ChaveEvento = tuple[str, Identificador] | tuple[str, Identificador, Identificador]


def _chave(evento: Evento) -> ChaveEvento:
    if type(evento) is EventoCurtida:
        return ('curtida', evento.usuario_id, evento.review_id)
    if type(evento) is EventoDerivada:
        return ('derivada', evento.review_id)
    raise ErroReputacao('Esperado EventoCurtida ou EventoDerivada')


def calcular_creditos(arvores: FlorestaReviews, evento: Evento) -> dict[Identificador, int]:
    """Calcula até três posições em O(1), sem mutações."""
    _chave(evento)
    no = arvores.consultar(evento.review_id)
    if isinstance(evento, EventoCurtida):
        if evento.usuario_id == no.autor_id:
            return {no.autor_id: 1}
    else:
        no = arvores.pai(no.review_id)
        if no is None:
            raise ErroReputacao('Derivação exige review com origem')
    creditos: dict[Identificador, int] = {}
    for pontos in (4, 2, 1):
        if no is None:
            break
        creditos[no.autor_id] = max(creditos.get(no.autor_id, 0), pontos)
        if pontos != 1:
            no = arvores.pai(no.review_id)
    return creditos


class Reputacao:
    """Eventos ativos e totais em memória, sem locks ou persistência."""

    def __init__(self) -> None:
        self._eventos: dict[ChaveEvento, dict[Identificador, int]] = {}
        self._totais: dict[Identificador, int] = {}

    def aplicar(self, arvores: FlorestaReviews, evento: Evento) -> bool:
        chave = _chave(evento)
        if chave in self._eventos:
            return False
        creditos = calcular_creditos(arvores, evento)
        self._eventos[chave] = creditos
        for autor, pontos in creditos.items():
            self._totais[autor] = self._totais.get(autor, 0) + pontos
        return True

    def remover(self, evento: Evento) -> bool:
        creditos = self._eventos.pop(_chave(evento), None)
        if creditos is None:
            return False
        for autor, pontos in creditos.items():
            total = self._totais[autor] - pontos
            if total:
                self._totais[autor] = total
            else:
                del self._totais[autor]
        return True

    def total(self, autor_id: Identificador) -> int:
        _validar_id(autor_id)
        return self._totais.get(autor_id, 0)

    def contribuicoes(self, evento: Evento) -> dict[Identificador, int] | None:
        creditos = self._eventos.get(_chave(evento))
        return None if creditos is None else creditos.copy()

    def totais(self) -> dict[Identificador, int]:
        return self._totais.copy()

    def reconstruir(self, arvores: FlorestaReviews, eventos_ativos: Iterable[Evento]) -> None:
        """Substitui estado após carga completa válida; falha preserva anterior."""
        nova = Reputacao()
        for evento in eventos_ativos:
            nova.aplicar(arvores, evento)
        self._eventos, self._totais = nova._eventos, nova._totais


reputacao_reviews = Reputacao()
