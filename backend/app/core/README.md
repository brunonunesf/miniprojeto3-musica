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

## Reputação — #43

`reputacao.py` fornece cálculo puro, `Reputacao` e o singleton
`reputacao_reviews`. Não importa banco/FastAPI nem altera a floresta.

```python
from app.core.reputacao import EventoCurtida, EventoDerivada, Reputacao

# Usando a floresta do exemplo acima: ana -> julia (apagada) -> pedro.
r = Reputacao()
evento = EventoCurtida('pedro', 99)
assert r.aplicar(arvores, evento)
assert r.contribuicoes(evento) == {3: 4, 2: 2, 1: 1}
assert not r.aplicar(arvores, evento)
assert r.remover(evento)
r.reconstruir(arvores, [EventoDerivada('pedro')])
assert r.totais() == {2: 4, 1: 2}
```

### Contrato

- Registros imutáveis: `EventoCurtida(review_id, usuario_id)` e
  `EventoDerivada(review_id)`. IDs seguem a #41: `int`/`str`, sem coerção,
  rejeitando booleanos. Chaves: `('curtida', usuario_id, review_id)` e
  `('derivada', review_id)`; tipos distintos nunca colidem.
- `calcular_creditos(arvores, evento)` retorna um dicionário novo autor/pontos.
  Curtida externa concede 4/2/1 ao autor/pai/avô; derivada concede 4/2/1 ao
  pai/avô/bisavô. Auto-curtida concede 1 somente ao autor. Autor repetido recebe
  somente a maior parcela por evento, sem redistribuição. Não percorre além das
  três posições; referências apagadas mantêm posição e crédito.
- Derivação de raiz e eventos malformados geram `ErroReputacao(ValueError)`;
  review ausente propaga `NoInexistente` da árvore. A entrada é uma floresta
  previamente validada pela #41. O core aceita eventos históricos de apagados;
  autorização para novas interações é responsabilidade do backend.
- `aplicar(arvores, evento)` retorna `True` se inseriu e `False` se já ativo.
  Repetição não recalcula créditos, mesmo se a árvore mudou. `remover(evento)`
  retorna se removeu e usa os créditos originalmente concedidos, sem consultar
  a árvore. Curtir/descurtir/recurtir deixa uma única contribuição ativa.
- `total(autor_id)` retorna zero para autor sem créditos. `totais()` e
  `contribuicoes(evento)` retornam cópias; esta última retorna `None` se ausente.
  Totais iguais a zero não ocupam o índice.
- `reconstruir(arvores, eventos_ativos)` calcula numa instância temporária e
  substitui todo o estado somente após sucesso. Aceita qualquer ordem,
  deduplica eventos, limpa com entrada vazia e preserva estado anterior diante
  de erro de validação ou falha do iterável. Usa a árvore atual, sem histórico
  de origens; repetir a mesma carga não infla os totais.

### Integração e limites

A #10 adapta os registros persistidos aos eventos, reconstrói no startup e
sincroniza após escrita confirmada, com recuperação entre banco e memória.
O PR #74 já usa a chave composta de curtida, mas sua exclusão física de reviews
remove curtidas: ainda precisa ser adaptada para conservar eventos pontuáveis e
referências (ID, autor, música e origem) após apagar conteúdo. Não reconstruir
somente a partir das curtidas sobreviventes enquanto essa adaptação não existir.

Excluir review não chama `remover`: preserva eventos de curtida e publicação
históricos. Descurtida válida remove sua contribuição. A remoção genérica não
é autorização de produto para retirar crédito de derivação. Reescuta,
comentário, follow e review raiz não produzem eventos de reputação.

A #51 selecionará os eventos afetados por mudança de origem e implementará sua
atualização retroativa. Pode reutilizar cálculo puro e contribuições; a
reconstrução completa é referência para validar os totais. A #43 não oferece
substituição atômica de subconjuntos. Chamadores devem garantir árvore estável
durante operações; não há locks, transações ou sincronização entre processos.

### Custos e validação

Com E registros de entrada, A eventos ativos e U autores pontuados: cálculo,
aplicação, remoção, contribuição individual e total têm O(1) esperado; cada
contribuição contém no máximo três autores. Reconstrução custa O(E) esperado e
O(A + U) de memória temporária, além do estado anterior até sucesso. Índices
ocupam O(A + U); `totais()` custa O(U). Custos não incluem construir a floresta.

```bash
cd backend
uv run python -m pytest tests_dados/test_reputacao.py -q
uv run python -m pytest tests_dados -q
uv run python -m pytest -q
```

## Recomendador de conteúdo — #55

`recomendador.py` fornece `Recomendador(catalogo)` e
`recomendar(usuario, reviews, curtidas) -> tuple[Sugestao, ...]`. Registros
`Musica`, `Review`, `Curtida` e `Sugestao` são dataclasses congeladas. IDs de
usuário/review são inteiros positivos (sem bool); música usa chave de catálogo.
Datas exigem fuso; adapter deve converter datas UTC ingênuas do SQLite para UTC
explicitamente, sem usar o fuso local. Não passar modelos ORM diretamente.

O backend fornece catálogo completo, reviews públicas/ativas e reviews do próprio
usuário (incluindo apagadas/privadas, se conservadas), além das curtidas atuais
necessárias às contagens globais. Referências de curtidas devem estar presentes
no snapshot; filtrar ambos os conjuntos conjuntamente. Reviews inelegíveis são
ignoradas como candidatas e sinais externos. Reviews próprias ativas continuam
sendo sinal e exclusão. Não enviar conteúdo textual, nota ou biblioteca privada.
A autorização e consistência transacional do snapshot são responsabilidade #23.

Duplicatas idênticas de reviews e curtidas são deduplicadas. Reviews conflitantes,
IDs inválidos, datas sem fuso e referências ausentes levantam `EntradaInvalida`.
Catálogo sem termos e catálogo vazio funcionam sem erro de vocabulário vazio.

Perfil reconstruído em toda consulta: própria ativa vale 3 por gravação;
curtidas externas em reviews elegíveis valem 1 por gravação quando não há própria.
Exclusão e descurtida operam pela remoção/alteração da entrada no próximo snapshot.
O índice só muda criando outra instância; a #23 deve construir e então substituir
no startup/alteração do catálogo, em todos os processos. Não há cache de perfis,
eventos, singleton obrigatório ou persistência neste módulo.

A saída completa contém chave, review representante, cosseno, motivo
(`afinidade`, `sem_sinais`, `sem_afinidade`) e até 3 termos prefixados de maior
contribuição. A API pagina **depois** do ranking e pode mapear termos a rótulos;
não deve expor snapshots ou contagens internas. O cosseno é afinidade vetorial,
sem interpretação probabilística. A escolha da review mais curtida não participa
do score. Mesmas entradas dão mesma ordem; mudanças entre páginas podem mover itens.

Custos: com T ocorrências de termos, Z entradas não nulas do índice, V termos,
R reviews, L curtidas deduplicadas, S gravações sinalizadas e C candidatas:
construção O(T + V log V + M log M), além da ordenação dos termos por documento;
memória O(Z + V + M). Por consulta, implementação conservadora custa
O(R + L log L + S(V + Z) + C V log V + C log C); matrizes esparsas evitam matriz
densa M×M, mas somas sucessivas do perfil e ordenação das contribuições não são
O(1). Memória adicional O(R + L + C + V). Não há atualização incremental.

Reprodução (sem banco):

```sh
uv run pytest tests_dados/test_recomendador.py -q
uv run python scripts/demo_recomendador.py
```
