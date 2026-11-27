"""Curadoria local. Sem --aplicar, executa em transação e desfaz a prévia."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=["listar", "executar", "migrar"])
    parser.add_argument("--arquivo", type=Path)
    parser.add_argument("--autor")
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--aplicacao-parada", action="store_true", help="obrigatório para fusão, para reconstruir árvores ao reiniciar")
    args = parser.parse_args()
    from app.db import Base, SessionLocal, atualizar_esquema_antigo, engine
    import app.models  # noqa: F401
    from app.models.catalogo_externo import AuditoriaCatalogo, ReferenciaExterna, RevisaoCorrespondencia, SolicitacaoInclusao
    from app.models.musica import Musica
    from app.services.curadoria_catalogo import Operacao, executar
    from pydantic import TypeAdapter
    from sqlalchemy import select

    if args.acao == "migrar":
        if not args.aplicar:
            print("Prévia: criar tabelas de referências/pedidos/revisões/auditoria e acrescentar três colunas em musicas; IDs preservados.")
            return 0
        Base.metadata.create_all(engine)
        atualizar_esquema_antigo()
        print("Esquema atualizado; nenhum catálogo foi importado.")
        return 0
    try:
        with SessionLocal() as db:
            if args.acao == "listar":
                def linhas(modelo, filtro=None):
                    consulta = select(modelo).order_by(modelo.id)
                    if filtro is not None:
                        consulta = consulta.where(filtro)
                    return [{c.name: getattr(x, c.name) for c in modelo.__table__.columns}
                            for x in db.scalars(consulta)]
                print(json.dumps({"pedidos": linhas(SolicitacaoInclusao),
                                  "musicas_pendentes": linhas(Musica, Musica.curadoria_estado == "pendente"),
                                  "correspondencias": linhas(RevisaoCorrespondencia),
                                  "referencias": linhas(ReferenciaExterna),
                                  "auditoria": linhas(AuditoriaCatalogo)}, ensure_ascii=False, default=str, indent=2))
                return 0
            if not args.arquivo or not args.autor:
                raise ValueError("executar exige --arquivo e --autor")
            operacoes = TypeAdapter(list[Operacao]).validate_python(json.loads(args.arquivo.read_text()))
            if args.aplicar and any(op.acao == "fundir" for op in operacoes) and not args.aplicacao_parada:
                raise ValueError("pare o backend e confirme --aplicacao-parada para fundir; reinicie para reconstruir as árvores")
            impactos = executar(db, operacoes, args.autor)
            print(json.dumps({"modo": "aplicado" if args.aplicar else "previa_revertida", "impactos": impactos}, ensure_ascii=False, indent=2))
            if args.aplicar:
                db.commit()
            else:
                db.rollback()
        return 0
    except Exception as erro:
        print(f"Curadoria não aplicada: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
