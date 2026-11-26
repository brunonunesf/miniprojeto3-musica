"""Massa determinística da #13. Sem imports de aplicação ou banco."""
import random
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from catalogo_musical import carregar_catalogo

VERSAO = "issue13-v1"
SEMENTE = 13
NOMES = [
    "Bruno Nunes", "Cecília Candeia", "Daniel Dantas", "Fernando Neto",
    "Gustavo Tenório", "Ítalo Matheus", "Sofia Lima", "Nicole Alverga",
    "Sofia Marques", "Pedro Luiz", "Lucas Todaro", "Davi Góes", "Matheus Brito",
    "Gabriel Esberard", "Eduardo Travassos", "Pedro Correia", "Henrique Guimarães",
    "Maria Laura", "Giorgio Nicolas", "Pedro Henrique", "Camila Batista",
    "Larissa Góes", "Rodrigo Ângelo", "Clarice Rodrigues", "Ryan Rodrigues",
]


def username(nome):
    return unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower().replace(" ", "_")


def preparar_cenario():
    rng = random.Random(SEMENTE)
    musicas = carregar_catalogo(Path(__file__).parent / "data/musicas_demo.json")
    usuarios = [dict(username=username(n), name=n, bio="Perfil fictício de demonstração") for n in NOMES]
    clareou = next(m['chave_catalogo'] for m in musicas if m['titulo'] == 'Clareou')
    posts = []
    inicio = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)

    def post(autor, musica, origem=None):
        indice = len(posts)
        posts.append(dict(chave=f"review-{indice+1:03}", autor=autor, musica=musica,
                          origem=origem, nota=indice % 11, texto="Opinião fictícia de demonstração: gostei desta indicação.",
                          created_at=(inicio + timedelta(minutes=indice)).isoformat()))

    for i, origem in enumerate([None, 'review-001', 'review-002', 'review-001', None]):
        post(usuarios[i]['username'], clareou, origem)
    ocupados = {(p['autor'], p['musica']) for p in posts}
    pares = [(u['username'], m['chave_catalogo']) for u in usuarios[:-1] for m in musicas
             if (u['username'], m['chave_catalogo']) not in ocupados]
    rng.shuffle(pares)
    for autor, musica in pares[:45]:
        post(autor, musica)
    follows = [(u['username'], v['username']) for u in usuarios[:-1] for v in usuarios[:-1] if u != v]
    rng.shuffle(follows)
    # Os protagonistas seguem a corrente, garantindo conteúdo no feed.
    fixos = [(usuarios[1]['username'], usuarios[0]['username']),
             (usuarios[2]['username'], usuarios[1]['username'])]
    follows = fixos + [p for p in follows if p not in fixos][:18]
    likes = [(u['username'], p['chave']) for u in usuarios[:-1] for p in posts if u['username'] != p['autor']]
    rng.shuffle(likes)
    cenario = dict(versao=VERSAO, semente=SEMENTE, usuarios=usuarios, musicas=musicas,
                   posts=posts, follows=[dict(seguidor=a, seguido=b) for a,b in follows],
                   likes=[dict(usuario=a, post=b) for a,b in likes[:30]])
    validar_cenario(cenario)
    return cenario


def validar_cenario(c):
    usuarios = {u['username'] for u in c['usuarios']}
    musicas = {m['chave_catalogo'] for m in c['musicas']}
    posts = {p['chave']: p for p in c['posts']}
    if (len(c['usuarios']) != len(usuarios) or len(c['musicas']) != len(musicas)
            or len(c['posts']) != len(posts)
            or len(usuarios) != 25 or len(musicas) != 20 or len(posts) != 50):
        raise ValueError('Contagens ou identidades inválidas')
    pares = [(p['autor'], p['musica']) for p in c['posts']]
    if len(set(pares)) != 50:
        raise ValueError('Review duplicada por pessoa/gravação')
    for p in posts.values():
        if type(p.get('nota')) is not int or not 0 <= p['nota'] <= 10:
            raise ValueError('Nota deve ser inteira de 0 a 10')
        if p['autor'] not in usuarios or p['musica'] not in musicas:
            raise ValueError('Referência inválida')
        visitados = {p['chave']}
        atual = p
        while atual['origem']:
            pai = posts.get(atual['origem'])
            if not pai or pai['musica'] != p['musica'] or pai['chave'] in visitados:
                raise ValueError('Origem inválida ou ciclo')
            visitados.add(pai['chave'])
            atual = pai
    for campo, chaves, minimo in [('follows', ('seguidor','seguido'),20), ('likes',('usuario','post'),30)]:
        pares = [tuple(r[k] for k in chaves) for r in c[campo]]
        if len(pares) < minimo or len(set(pares)) != len(pares):
            raise ValueError('Relações insuficientes ou duplicadas')
        for a,b in pares:
            if a not in usuarios or b not in (usuarios if campo == 'follows' else posts) or (campo == 'follows' and a == b):
                raise ValueError('Relação inválida')
    novo = username(NOMES[-1])
    if any(p['autor'] == novo for p in posts.values()) or any(l['usuario'] == novo for l in c['likes']):
        raise ValueError('Conta nova contém sinais')
