"""Testes isolados: fora de tests/ para não carregar seu conftest de API/banco."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from catalogo_musical import CATALOGO_PADRAO, ErroCatalogo, carregar_catalogo, validar_catalogo


@pytest.fixture
def entrada():
    return json.loads(CATALOGO_PADRAO.read_text(encoding="utf-8"))[0]


def test_catalogo_atual_e_identidades():
    registros = carregar_catalogo()
    assert len(registros) == 6
    assert len({r['chave_catalogo'] for r in registros}) == 6
    aurora = [r for r in registros if r['artista'] == 'Aurora do Vale']
    assert {r['tipo_versao'] for r in aurora} == {'original', 'remix', 'ao_vivo', 'remaster'}
    horizonte = [r for r in registros if r['titulo'] == 'Horizonte']
    assert len({r['artista'] for r in horizonte}) == 2


def test_normalizacao_nao_muda_chave_ou_entrada(entrada):
    entrada.update(titulo='  Um   título\t ', artista=' Artista\nTeste ',
                   generos=[' Indie ', 'INDIE', ' MPB '], tags=[' Voz ', 'VOZ', ' ao   vivo '])
    original = copy.deepcopy(entrada)
    registro = validar_catalogo([entrada])[0]
    assert registro['titulo'] == 'Um título' and registro['artista'] == 'Artista Teste'
    assert registro['generos'] == ['indie', 'mpb']
    assert registro['tags'] == ['voz', 'ao vivo']
    assert registro['chave_catalogo'] == original['chave_catalogo']
    assert entrada == original
    assert validar_catalogo([registro]) == [registro]


@pytest.mark.parametrize(('campo', 'valor'), [
    ('titulo', '  '), ('artista', ''), ('titulo', 'x' * 201), ('artista', 'x' * 201),
    ('descricao_versao', 'x' * 201), ('tipo_versao', 'desconhecida'),
    ('chave_catalogo', 'X inválida'), ('chave_catalogo', 'x' * 101),
    ('generos', []), ('tags', []), ('generos', [' ']), ('tags', ['x' * 81]),
    ('generos', 'indie'), ('tags', [12]), ('artista', None),
])
def test_campos_invalidos_identificados(entrada, campo, valor):
    with pytest.raises(ErroCatalogo, match=rf'entrada 1, campo {campo}'):
        validar_catalogo([{**entrada, campo: valor}])


@pytest.mark.parametrize('campo', ['chave_catalogo', 'titulo', 'artista', 'tipo_versao', 'descricao_versao', 'generos', 'tags'])
def test_campo_obrigatorio(entrada, campo):
    del entrada[campo]
    with pytest.raises(ErroCatalogo, match=rf'entrada 1, campo {campo}'):
        validar_catalogo([entrada])


@pytest.mark.parametrize('versao', ['remix', 'ao_vivo', 'remaster'])
def test_versao_precisa_descricao(entrada, versao):
    with pytest.raises(ErroCatalogo, match='campo descricao_versao'):
        validar_catalogo([{**entrada, 'tipo_versao': versao, 'descricao_versao': '  '}])


def test_rejeita_duplicata_sem_retornar_conjunto_parcial(entrada):
    with pytest.raises(ErroCatalogo, match='entrada 2, campo chave_catalogo.*entrada 1'):
        validar_catalogo([entrada, entrada])
    with pytest.raises(ErroCatalogo, match='entrada 2, campo titulo'):
        validar_catalogo([entrada, {**entrada, 'chave_catalogo': 'outra', 'titulo': ''}])


def test_nao_deduplica_por_metadados(entrada):
    outra = {**entrada, 'chave_catalogo': 'outra-gravacao'}
    assert len(validar_catalogo([entrada, outra])) == 2
    corrigida = {**entrada, 'titulo': 'Título corrigido', 'tags': ['outra tag']}
    assert validar_catalogo([corrigida])[0]['chave_catalogo'] == entrada['chave_catalogo']


@pytest.mark.parametrize('conteudo', [{}, [], None, 'musica', [12]])
def test_formato_invalido(conteudo):
    with pytest.raises(ErroCatalogo):
        validar_catalogo(conteudo)


def test_arquivos_invalidos(tmp_path):
    arquivo = tmp_path / 'catalogo.json'
    arquivo.write_text('[', encoding='utf-8')
    with pytest.raises(ErroCatalogo, match='linha 1, coluna'):
        carregar_catalogo(arquivo)
    arquivo.write_bytes(b'\xff')
    with pytest.raises(ErroCatalogo, match='UTF-8'):
        carregar_catalogo(arquivo)
    with pytest.raises(ErroCatalogo, match='não foi possível ler'):
        carregar_catalogo(tmp_path / 'ausente.json')


def test_cli_sucesso_e_erro_sem_gravar(tmp_path, entrada):
    arquivo = tmp_path / 'catalogo.json'
    arquivo.write_text(json.dumps([entrada]), encoding='utf-8')
    antes = arquivo.read_bytes()
    comando = [sys.executable, str(BACKEND / 'scripts' / 'validar_catalogo.py'), str(arquivo)]
    sucesso = subprocess.run(comando, cwd=tmp_path, capture_output=True, text=True)
    assert sucesso.returncode == 0 and '1 entradas' in sucesso.stdout
    assert arquivo.read_bytes() == antes
    arquivo.write_text(json.dumps([{**entrada, 'titulo': ''}]), encoding='utf-8')
    falha = subprocess.run(comando, cwd=tmp_path, capture_output=True, text=True)
    assert falha.returncode == 1 and 'entrada 1, campo titulo' in falha.stderr
    assert set(p.name for p in tmp_path.iterdir()) == {'catalogo.json'}


def test_carregamento_independente_de_app_e_banco(tmp_path):
    codigo = f'''
import sys
sys.path.insert(0, {str(BACKEND)!r})
class BloquearAplicacao:
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {{'app', 'sqlalchemy', 'fastapi', 'sqlite3'}}:
            raise AssertionError('Dependência proibida: ' + fullname)
sys.meta_path.insert(0, BloquearAplicacao())
from catalogo_musical import carregar_catalogo
assert len(carregar_catalogo()) == 6
'''
    resultado = subprocess.run([sys.executable, '-B', '-c', codigo], cwd=tmp_path, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stderr
    assert list(tmp_path.iterdir()) == []


def test_capa_opcional_sem_quebrar_catalogo_anterior(entrada):
    entrada.pop('capa_url', None)
    original = copy.deepcopy(entrada)
    assert validar_catalogo([entrada])[0]['capa_url'] is None
    assert entrada == original
    assert validar_catalogo([{**entrada, 'capa_url': None}])[0]['capa_url'] is None


@pytest.mark.parametrize('url', [
    'https://images.example.com/capa.jpg',
    'http://images.example.com/capa.png?versao=2',
])
def test_capa_url_json_e_identidade_preservadas(entrada, url):
    entrada['capa_url'] = url
    original = copy.deepcopy(entrada)
    registro = validar_catalogo([entrada])[0]
    assert registro['capa_url'] == url
    assert registro['chave_catalogo'] == entrada['chave_catalogo']
    assert entrada == original
    assert json.loads(json.dumps(registro)) == registro
    assert validar_catalogo([registro]) == [registro]


@pytest.mark.parametrize('url', [
    '', ' ', 'capa.jpg', '/capas/capa.png', 'ftp://example.com/capa.jpg',
    'data:image/png;base64,abc', 'javascript:alert(1)',
    'https://', 123, 'https://example.com/' + 'a' * 2048,
])
def test_rejeita_capa_invalida_com_diagnostico(entrada, url):
    with pytest.raises(ErroCatalogo, match='entrada 1, campo capa_url'):
        validar_catalogo([{**entrada, 'capa_url': url}])
