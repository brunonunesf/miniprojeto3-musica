"""Demonstração determinística da #55; não acessa banco nem prova gosto real."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.recomendador import Musica, Recomendador, Review, Curtida


def main():
    data = datetime(2026, 11, 26, tzinfo=timezone.utc)
    catalogo = [Musica('analisada', 'Aurora', ('indie',), ('guitarra',)),
                Musica('relacionada', 'Maré', ('indie',), ('guitarra',)),
                Musica('distante', 'Trio', ('jazz',), ('piano',))]
    reviews = [Review(1, 'analisada', 1, data), Review(2, 'relacionada', 2, data),
               Review(3, 'relacionada', 3, data), Review(4, 'distante', 2, data)]
    motor = Recomendador(catalogo)
    linhas = []
    for nome, usuario, likes in [('personalizado', 1, [Curtida(9, 2)]),
                                 ('conta_nova', 8, []), ('descurtida', 1, [])]:
        saida = motor.recomendar(usuario, reviews, likes)
        if usuario == 1:
            assert [s.musica for s in saida] == ['relacionada', 'distante']
            assert saida[0].similaridade > 0 and saida[1].similaridade == 0
            assert saida[0].review_id == (2 if likes else 3)
        else:
            assert all(s.motivo == 'sem_sinais' for s in saida)
        linhas.append({'cenario': nome, 'resultado': [
            {'musica': s.musica, 'review': s.review_id, 'cosseno': s.similaridade,
             'motivo': s.motivo, 'caracteristicas': s.caracteristicas} for s in saida]})
    print(json.dumps(linhas, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
