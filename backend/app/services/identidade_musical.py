"""Regras de dados: nenhuma dependência de banco ou rede."""
import re
import unicodedata

from app.schemas.catalogo_externo import FaixaExterna


def normalizar(texto: str) -> str:
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", texto)
                            if not unicodedata.combining(c)).casefold().split())


def versao_explicita(titulo: str, versao: str = "") -> tuple[str, str]:
    # Ausência de rótulo não comprova gravação original.
    texto = normalizar(versao or titulo)
    for tipo, padrao in (("remaster", r"remaster(?:ed|izado)?"), ("remix", r"remix"),
                         ("ao_vivo", r"ao vivo|\blive\b"), ("original", r"original (?:mix|version)|versao original")):
        if re.search(padrao, texto):
            return tipo, versao or titulo
    return "desconhecida", versao


def mesma_gravacao(a: FaixaExterna, b: FaixaExterna) -> bool:
    if (a.servico, a.id_externo) == (b.servico, b.id_externo):
        return True
    return bool(
        a.servico != b.servico and a.isrc and a.isrc == b.isrc
        and {normalizar(x) for x in a.artistas} == {normalizar(x) for x in b.artistas}
        and a.duracao_ms is not None and b.duracao_ms is not None
        and abs(a.duracao_ms - b.duracao_ms) <= 2000
        and a.tipo_versao != "desconhecida" and a.tipo_versao == b.tipo_versao
        and normalizar(a.titulo) == normalizar(b.titulo)
        and bool(a.descricao_versao) and normalizar(a.descricao_versao) == normalizar(b.descricao_versao)
    )
