"""Seed da demonstração: preflight obrigatório, sem carga parcial."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cenarios_demo import preparar_cenario
from seed_demo import IntegracaoPendente, seed_fake


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validar-demo', action='store_true')
    parser.add_argument('--reset-demo', action='store_true')
    args = parser.parse_args()
    if args.validar_demo and args.reset_demo:
        parser.error('Escolha validação ou reset')
    if args.validar_demo:
        c = preparar_cenario()
        print('Cenário válido:', ', '.join(f'{len(c[k])} {k}' for k in ('usuarios','musicas','posts','follows','likes')))
        return 0
    from app.db import SessionLocal, engine
    # Caminho reservado exclusivamente à demonstração; nunca aceita o app.db.
    alvo = Path(__file__).resolve().parents[1] / 'demo' / 'issue13.db'
    if engine.url.get_backend_name() != 'sqlite' or not engine.url.database or Path(engine.url.database).resolve() != alvo:
        print(f'Use DATABASE_URL=sqlite:///{alvo}; nenhum dado foi alterado.', file=sys.stderr)
        return 1
    if args.reset_demo:
        # Não apagar dados antes de existir um adaptador capaz de reconstruí-los.
        print('Reset indisponível: adaptador de persistência ainda pendente; banco preservado.', file=sys.stderr)
        return 1
    alvo.parent.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        try:
            print(seed_fake(db))
        except IntegracaoPendente as exc:
            print(exc, file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
