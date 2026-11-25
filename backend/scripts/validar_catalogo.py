"""Execute com o Python do backend; não usa banco, API ou sessão."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalogo_musical import CATALOGO_PADRAO, ErroCatalogo, carregar_catalogo  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida o catálogo musical da issue #9, sem gravar dados.")
    parser.add_argument("arquivo", nargs="?", type=Path, default=CATALOGO_PADRAO)
    args = parser.parse_args()
    try:
        registros = carregar_catalogo(args.arquivo)
    except ErroCatalogo as exc:
        print(f"Catálogo inválido:\n{exc}", file=sys.stderr)
        return 1
    print(f"Catálogo válido: {len(registros)} entradas. Nenhum arquivo ou banco foi alterado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
