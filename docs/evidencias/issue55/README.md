# Validação local — #55

Reprodução na raiz do repositório:

```sh
cd backend
uv sync --frozen
uv run pytest tests_dados/test_recomendador.py -q
uv run python scripts/demo_recomendador.py
uv run pytest -q
```

`demo.json` registra a execução real do cenário de código fixo em
`scripts/demo_recomendador.py`. Não usa API, banco ou mocks de serviço. O catálogo
e as interações são sintéticos; não representam avaliação de gosto de pessoas reais.

Resultado de referência: relacionada antes de distante, cosseno
0.5363499141045835 contra zero; conta nova usa `sem_sinais`. Descurtida muda a
representante de ID 2 para ID 3 sem alterar a afinidade. O script verifica essas
condições com assertions. O teste de pesos usa vetores ortogonais e oráculo
3/√10 e 1/√10; o teste TF-IDF calcula IDFs e cosseno independentemente.

Validação de dados: 208 testes aprovados, incluindo 19 cenários do recomendador.
Sem nova rota, tela ou migração; estes resultados não comprovam integração #23.

Suíte completa: **400 aprovados** em 136,21 s; aviso preexistente de depreciação
Starlette/TestClient com HTTPX. Essa execução coletou 17 testes do recomendador;
os dois cenários finais (substituição do índice e diversidade restrita ao fallback)
foram executados depois na suíte de dados de 208 aprovados e na execução específica
final de **19 aprovados**. `uv sync --frozen`, `uv lock --check`, compilação Python,
demonstração e `git diff --check` aprovados. Nenhum banco pessoal acessado:
a suíte de API configura SQLite temporário no seu conftest.
