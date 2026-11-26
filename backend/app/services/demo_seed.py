"""Adaptador da carga completa aos modelos oficiais, incluindo origens da #78."""
from datetime import datetime, timezone

import bcrypt
from sqlalchemy import func, inspect, select, text

import app.models  # registra todos os modelos oficiais antes de criar esquema
from app.db import Base
from app.models.user import User
from app.models.musica import Musica
from app.models.post import Post
from app.models.follow import Follow
from app.models.curtida import Curtida
from app.models.review_apagada import ReviewApagada
from app.core.arvores import FlorestaReviews, RegistroReview
from app.schemas.post import PostCreate
from app.services.auth import gerar_hash
from catalogo_musical import carregar_catalogo
from cenarios_demo import validar_cenario
from seed_demo import IntegracaoPendente, SENHA_DEMO

MODELOS = (User, Musica, Post, Follow, Curtida, ReviewApagada)


def _musica(registro):
    return {**registro, 'capa_url': registro.get('capa_url') or ''}


def _exigir(condicao, mensagem):
    if not condicao:
        raise IntegracaoPendente(mensagem)


class AdaptadorBackend:
    def verificar_requisitos(self, cenario):
        validar_cenario(cenario)
        floresta = FlorestaReviews()
        floresta.reconstruir(RegistroReview(p['chave'], p['musica'], p['autor'], p['origem'])
                            for p in cenario['posts'])
        _exigir(carregar_catalogo() == cenario['musicas'],
                'Catálogo diferente da demo. Configure CATALOGO_MUSICAL_PATH=data/musicas_demo.json '
                'no seed e na aplicação; não importar o catálogo fictício nesta base.')

    def preparar_banco(self, engine):
        # Somente no temporário novo do reset, nunca altera esquema existente.
        Base.metadata.create_all(engine)

    def verificar(self, db, cenario):
        self.verificar_requisitos(cenario)
        conexao = db.connection()
        _exigir(conexao.dialect.name == 'sqlite', 'Adaptador validado somente para SQLite')
        _exigir(db.scalar(text('PRAGMA foreign_keys')) == 1, 'Ative foreign_keys por conexão')
        _exigir(not db.execute(text('PRAGMA foreign_key_check')).first(),
                'Banco contém referências inválidas; dados existentes foram preservados')
        esquema = inspect(conexao)
        for modelo in MODELOS:
            tabela = modelo.__table__
            _exigir(esquema.has_table(tabela.name), f'Tabela ausente: {tabela.name}')
            colunas = {c['name'] for c in esquema.get_columns(tabela.name)}
            _exigir(set(tabela.columns.keys()) <= colunas, f'Esquema incompatível: {tabela.name}')
            pk = set(esquema.get_pk_constraint(tabela.name)['constrained_columns'])
            _exigir(pk == {c.name for c in tabela.primary_key}, f'Chave primária incompatível: {tabela.name}')
            esperadas = {(coluna.name, fk.column.table.name, fk.column.name)
                         for coluna in tabela.columns for fk in coluna.foreign_keys}
            reais = {(local, fk['referred_table'], remoto)
                     for fk in esquema.get_foreign_keys(tabela.name)
                     for local, remoto in zip(fk['constrained_columns'], fk['referred_columns'])}
            _exigir(esperadas <= reais, f'Chave estrangeira ausente: {tabela.name}')
        for modelo, campos in ((User, {'username'}), (Musica, {'chave_catalogo'}),
                               (Post, {'autor_id', 'musica_id'})):
            unicas = [set(u['column_names']) for u in esquema.get_unique_constraints(modelo.__tablename__)]
            unicas.extend(set(i['column_names']) for i in esquema.get_indexes(modelo.__tablename__) if i['unique'])
            _exigir(campos in unicas, f'Restrição única ausente: {modelo.__tablename__}')
        ddl = db.scalar(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='posts'"))
        _exigir(ddl and 'AUTOINCREMENT' in ddl.upper(), 'Posts sem AUTOINCREMENT; use reset do banco de demo')
        for modelo in (User, Post, Follow, Curtida, ReviewApagada):
            _exigir(not db.scalar(select(func.count()).select_from(modelo)),
                    f'Colisão: {modelo.__tablename__} já contém dados sem carga aplicada; banco preservado')
        existentes = list(db.scalars(select(Musica)))
        por_chave = {m['chave_catalogo']: _musica(m) for m in cenario['musicas']}
        for musica in existentes:
            esperado = por_chave.get(musica.chave_catalogo)
            _exigir(esperado is not None, 'Banco contém música fora do catálogo de demonstração')
            _exigir(all(getattr(musica, k) == v for k, v in esperado.items()),
                    f'Colisão de identidade/metadados: {musica.chave_catalogo}')

    def gravar(self, db, cenario, senha):
        self.verificar(db, cenario)  # protege também chamadas diretas
        hash_demo = gerar_hash(senha)  # senha pública e exclusiva da demonstração
        usuarios = {}
        for registro in cenario['usuarios']:
            usuario = User(**registro, password_hash=hash_demo)
            db.add(usuario)
            usuarios[usuario.username] = usuario
        musicas = {m.chave_catalogo: m for m in db.scalars(select(Musica))}
        for registro in cenario['musicas']:
            if registro['chave_catalogo'] not in musicas:
                musica = Musica(**_musica(registro))
                db.add(musica)
                musicas[musica.chave_catalogo] = musica
        db.flush()
        posts = {}
        from graphlib import TopologicalSorter
        por_chave = {p['chave']: p for p in cenario['posts']}
        ordem = TopologicalSorter({p['chave']: [p['origem']] if p['origem'] else []
                                   for p in cenario['posts']}).static_order()
        for chave in ordem:
            registro = por_chave[chave]
            origem_id = posts[registro['origem']].id if registro['origem'] else None
            dados = PostCreate(musica_id=musicas[registro['musica']].id,
                               nota=registro['nota'], texto=registro['texto'], origem_id=origem_id)
            post = Post(**dados.model_dump(), autor_id=usuarios[registro['autor']].id,
                        created_at=datetime.fromisoformat(registro['created_at']))
            db.add(post)
            db.flush()  # ID real disponível antes de inserir descendentes
            posts[registro['chave']] = post
        db.flush()
        db.add_all(Follow(seguidor_id=usuarios[r['seguidor']].id, seguido_id=usuarios[r['seguido']].id)
                   for r in cenario['follows'])
        db.add_all(Curtida(usuario_id=usuarios[r['usuario']].id, post_id=posts[r['post']].id)
                   for r in cenario['likes'])
        db.flush()

    def validar(self, db, cenario):
        self.verificar_requisitos(cenario)
        usuarios = {u.username: u for u in db.scalars(select(User))}
        _exigir(set(usuarios) == {u['username'] for u in cenario['usuarios']}, 'Usuários divergentes')
        hashes = set()
        for u in cenario['usuarios']:
            real = usuarios[u['username']]
            _exigir(real.name == u['name'] and real.bio == u['bio'], 'Perfil divergente')
            hashes.add(real.password_hash)
        _exigir(all(h and bcrypt.checkpw(SENHA_DEMO.encode(), h.encode()) for h in hashes),
                'Credenciais de demonstração inválidas')
        musicas = {m.chave_catalogo: m for m in db.scalars(select(Musica))}
        _exigir(set(musicas) == {m['chave_catalogo'] for m in cenario['musicas']}, 'Catálogo divergente')
        for m in cenario['musicas']:
            _exigir(all(getattr(musicas[m['chave_catalogo']], k) == v for k, v in _musica(m).items()),
                    'Metadados musicais divergentes')
        reais = list(db.scalars(select(Post)))
        por_par = {(p.autor_id, p.musica_id): p for p in reais}
        _exigir(len(reais) == len(por_par) == len(cenario['posts']), 'Reviews divergentes')
        por_chave = {}
        for p in cenario['posts']:
            real = por_par.get((usuarios[p['autor']].id, musicas[p['musica']].id))
            _exigir(real is not None and real.nota == p['nota'] and real.texto == p['texto'],
                    'Conteúdo de review divergente')
            data = real.created_at
            if data.tzinfo is None:
                data = data.replace(tzinfo=timezone.utc)
            _exigir(data == datetime.fromisoformat(p['created_at']), 'Data de review divergente')
            por_chave[p['chave']] = real
        for p in cenario['posts']:
            esperado = por_chave[p['origem']].id if p['origem'] else None
            _exigir(por_chave[p['chave']].origem_id == esperado, 'Origem de review divergente')
        follows = {(r.seguidor_id, r.seguido_id) for r in db.scalars(select(Follow))}
        _exigir(follows == {(usuarios[r['seguidor']].id, usuarios[r['seguido']].id)
                           for r in cenario['follows']}, 'Follows divergentes')
        curtidas = {(r.usuario_id, r.post_id) for r in db.scalars(select(Curtida))}
        _exigir(curtidas == {(usuarios[r['usuario']].id, por_chave[r['post']].id)
                            for r in cenario['likes']}, 'Curtidas divergentes')


def criar_adaptador():
    return AdaptadorBackend()
