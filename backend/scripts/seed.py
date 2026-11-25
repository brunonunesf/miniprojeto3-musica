"""Seed da demonstração: preflight obrigatório, sem carga parcial."""
import argparse
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cenarios_demo import preparar_cenario
from seed_demo import IntegracaoPendente, seed_fake, carregar_adaptador, preparar_validar_banco
from reset_demo import ErroReset, verificar_alvo, resetar_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validar-demo', action='store_true')
    parser.add_argument('--reset-demo', action='store_true')
    parser.add_argument('--confirmar-reset', action='store_true')
    parser.add_argument('--aplicacao-parada', action='store_true')
    args = parser.parse_args()
    if (args.confirmar_reset or args.aplicacao_parada) and not args.reset_demo:
        parser.error('Confirmações só podem acompanhar --reset-demo')
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
    try:
        verificar_alvo(Path(engine.url.database), alvo)
        if args.reset_demo:
            # Resolver dependências antes de criar temporário ou tocar no banco existente.
            if not args.confirmar_reset or not args.aplicacao_parada:
                raise ErroReset('Exige --confirmar-reset e --aplicacao-parada')
            adaptador = carregar_adaptador()
            engine.dispose()
            backup = resetar_demo(
                alvo, alvo, lambda caminho: preparar_validar_banco(caminho, adaptador),
                confirmar=args.confirmar_reset, aplicacao_parada=args.aplicacao_parada,
            )
            print(f'Banco reconstruído: {alvo}; backup: {backup or "não havia banco anterior"}')
        else:
            # Evitar até mesmo abrir/criar arquivo quando faltar adaptador.
            adaptador = carregar_adaptador()
            if not alvo.exists():
                resetar_demo(
                    alvo, alvo, lambda caminho: preparar_validar_banco(caminho, adaptador),
                    confirmar=True, aplicacao_parada=True,
                )
                print(f'Banco inicial preparado e validado: {alvo}')
            else:
                with SessionLocal() as db:
                    print(seed_fake(db, adaptador))
    except (IntegracaoPendente, ErroReset, OSError, sqlite3.Error) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
