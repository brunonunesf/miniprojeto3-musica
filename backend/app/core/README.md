# core/: as estruturas de dados do time

Aqui ficam as estruturas de dados das features, em Python puro: sem
SQLAlchemy, sem FastAPI, sem import de banco. Só dicts, sets, listas, deques,
heaps e a lógica deles. A banca olha isso no critério de organização do código: a lógica das
estruturas fica aqui, e o endpoint a usa de verdade.

## O padrão

`contadores.py` é o exemplo. Cada estrutura segue cinco regras:

1. É uma classe ou módulo puro, testável sem servidor.
2. Existe uma instância global (singleton de módulo) que a API usa.
3. No startup (lifespan, em `main.py`), o singleton é reconstruído a partir do
   banco. A memória zera a cada restart, o banco não.
4. Todo write relevante da API atualiza o singleton em O(1), sem reconstruir
   tudo em O(n).
5. O endpoint importa e usa o singleton (`from app.core...`).

## Avisos

- `uvicorn --reload` reinicia o processo a cada save. O singleton zera e é
  reconstruído no startup. Se os números sumirem, é isso (guia 04).
- Em produção, isso seria um índice ou uma consulta no banco. Aqui a estrutura
  fica em memória porque o objetivo é vocês a implementarem e medirem.
- Reconstruir a estrutura a cada request só é aceitável se o Big O declarado no
  `DECISIONS.md` disser isso. Nesse caso a operação é O(n), não O(1).

## Árvores de recomendações — #41

`arvores.py` fornece `FlorestaReviews` e o singleton `arvores_reviews`. É uma
**floresta**: a mesma música pode ter várias raízes. Somente reviews viram nós;
curtidas, comentários e reescutas ficam fora da entrada. Não há conteúdo textual
nos registros, apenas identidade, autoria, origem e estado de exclusão.

```python
from app.core.arvores import FlorestaReviews, RegistroReview

arvores = FlorestaReviews()
arvores.reconstruir([
    RegistroReview('ana', 'faixa-original', 1),
    RegistroReview('julia', 'faixa-original', 2, origem_id='ana'),
    RegistroReview('pedro', 'faixa-original', 3, origem_id='julia'),
])
arvores.marcar_apagada('julia')
pagina = arvores.descendentes('ana', ordem='bfs', limit=50)
assert [(p.no.review_id, p.distancia) for p in pagina.itens] == [
    ('julia', 1), ('pedro', 2),
]
assert pagina.itens[0].no.apagada
assert not pagina.tem_mais
assert arvores.raiz('pedro').review_id == 'ana'
```

### Interface de dados

- `RegistroReview(review_id, musica_id, autor_id, origem_id=None, apagada=False)`:
  registro imutável. IDs são `int` ou `str` (booleanos não são aceitos), sem
  coerção: `1` e `'1'` são IDs distintos. `None` em origem significa raiz.
  A identidade da música deve ser a chave interna da mesma gravação acordada
  na #39; títulos iguais ou versões diferentes não autorizam uma ligação.
- `reconstruir(iterable_de_registros)`: aceita qualquer ordem de parentesco,
  inclusive referências apagadas, mas exige todos os pais presentes. Valida a
  carga completa em estrutura temporária; qualquer erro preserva o estado
  anterior. Não trata pai ausente como raiz nem inventa referência apagada.
  Entrada vazia limpa a floresta. Irmãos e raízes seguem a ordem de entrada;
  o backend deve carregar em ordem estável (por exemplo, data e ID).
- `inserir(registro)`: ID novo, origem existente, ativa e da mesma música.
  Um ID novo ligado a um pai existente não pode formar ciclo. Não é upsert.
  `marcar_apagada(id)` é idempotente e mantém autoria, pai e filhos; retorna o
  registro atualizado. A reconstrução aceita filhos históricos de pais apagados.
- `consultar(id)`, `pai(id)` e `raiz(id)` devolvem registros imutáveis;
  `pai` retorna `None` para raiz. `raizes(musica_id)` devolve uma tupla, vazia
  se não houver raízes. Essas consultas de identidade não são paginadas.
- `ancestrais(id, *, offset=0, limit=50, profundidade_maxima=None)` percorre do
  pai à raiz. `descendentes` recebe os mesmos parâmetros mais `ordem='bfs'`
  ou `'dfs'` (pré-ordem). Ambos excluem o nó inicial e retornam
  `Pagina(itens: tuple[Passo, ...], tem_mais: bool)`;
  `Passo(no, distancia)` usa distância estrutural, sem descontar apagados.
- `limit`: inteiro de 1 a 200; `offset`: inteiro não negativo;
  `profundidade_maxima`: inteiro não negativo ou `None`, sem corte por padrão.
  Profundidade zero produz vazio. A profundidade filtra antes da paginação;
  offset além do fim retorna vazio. `tem_mais` considera somente os resultados
  elegíveis no limite de profundidade. Não há total nem cursor persistente.
- `NoInexistente`, `EstruturaInvalida` e `ParametroInvalido` derivam de
  `ErroArvore(ValueError)`. Erros estruturais incluem duplicatas, pai ausente,
  outra música e ciclos. Parâmetros do percurso são validados antes da busca
  pelo nó. Retornos não permitem alterar os índices internos.

### Integração e limites de responsabilidade

A #10 implementará o adaptador de modelos para registros e a reconstrução no
startup. Deve chamar as mutações somente após confirmação da escrita e garantir
consistência/recuperação entre banco e memória. Este módulo não implementa
transações, locks ou sincronização entre processos. A paginação reflete o estado
atual; mutações entre páginas podem mudar posição ou pertencimento dos nós.

Texto próprio, permissão, existência de usuário/música e unicidade de review
**ativa** por pessoa/gravação são validações do backend. O core permite conservar
um registro apagado e inserir uma nova raiz com mesmo autor/música. O backend
apaga o conteúdo e os avisos; não deve apagar o registro estrutural.

A #49 implementará troca de origem e movimentação de subárvore. A #41 não
permite editar o pai de um registro existente. Reputação é calculada por outra
estrutura; os percursos preservam os ancestrais apagados para esse consumo.

### Custos e testes

Com `n` nós, `h` altura e `r` raízes da música:

| Operação | Tempo | Memória adicional |
| --- | --- | --- |
| Reconstrução e validação completa | O(n) esperado | O(n), mantendo também estado anterior até sucesso |
| Inserir, consultar, pai, marcar apagada | O(1) esperado/amortizado | O(1) por operação |
| Raiz | O(h) | O(1) |
| Listar raízes | O(r) | O(r) para a tupla |
| Ancestrais paginados | O(a), ancestrais examinados | O(limit) para saída |
| Descendentes BFS/DFS | O(v + e), nós retirados e ligações enfileiradas | O(f + limit), fronteira pendente |

Índices usam O(n) memória. A reconstrução detecta ciclos com caminhos concluídos
para evitar O(n²) em correntes. Não há recursão. Paginação precisa atravessar o
offset e consultar um item extra para determinar `tem_mais`. Um nó com muitos
filhos pode colocar todos na fronteira mesmo com uma página pequena; BFS e DFS
podem usar O(n) memória auxiliar no pior caso. Não prometemos O(limit) de tempo.

```bash
cd backend
uv run pytest tests_dados/test_arvores.py -v
uv run pytest tests_dados -q
```

Os testes ficam fora de `tests/` para não carregar o conftest de API/banco.
`make test` inclui `tests/` e `tests_dados/` pela configuração do pytest.
O conftest de `tests/` não se aplica aos testes em `tests_dados/`; a execução
isolada acima continua disponível para validar o core sem iniciar a suíte de API.
