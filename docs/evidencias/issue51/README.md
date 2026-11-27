# Aceite da issue #51

A estratégia mantida é a reconstrução completa já integrada pelo PR #97. A #51 exige resultados corretos e documentação de custo; não exige atualização incremental. A auditoria acrescenta disponibilidade e recuperação para que uma troca persistida não exponha créditos antigos como atuais.

| Critério | Evidência automatizada |
| --- | --- |
| Eventos da review movida e descendentes, fórmula 4/2/1 | `test_recalculo_completo_bate_com_oraculo_por_evento` compara cada contribuição e o total com um cálculo independente sobre registros do banco |
| Sem duplicar autores/caminhos, maior parcela | `test_autor_repetido_e_ancestrais_compartilhados`, além dos testes de fórmula do núcleo |
| Preservar eventos reais e apagados | Comparação das chaves antes/depois; descendente apagado conserva sua curtida histórica e sua derivação |
| Descurtidas, repetição e mover de volta | Oráculo após movimentos, retorno exato aos totais anteriores e retirada de curtida já recalculada |
| Recuperação e reinício | Falhas injetadas de árvore, cálculo, SQL e startup; consulta seguinte e repetição do pedido recuperam sem evento novo |
| Sem publicar totais antigos | Perfil HTTP 200 com `reputacao: null`; resposta de troca contém origem salva e `reputacao_disponivel: false` |
| Interface | Testes focados em desktop e 360 px verificam aviso de origem salva, ocultação de número antigo e botão de recuperação |

## Reprodução

Na raiz:

```sh
cd backend
uv run pytest -q
uv run pytest tests/test_recalculo_reputacao.py -q
```

No frontend:

```sh
npm ci
npm run typecheck
npm run build
PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/origem-descobrir.spec.ts --grep 'reputação é buscada|autora corrige|perfil sem reputação'
```

O Playwright usa banco descartável e autenticação real; as respostas específicas de perfil/correção são simuladas para controlar falhas. A prova das falhas de persistência e recálculo está nos testes de API com banco descartável, não em navegação com falha real do servidor.

## Resultado desta implementação

- Suíte completa do backend: **499 aprovados**, 1 aviso preexistente de depreciação Starlette/httpx (264,12 s). Essa execução foi iniciada antes da adição dos dois últimos casos; a coleta final contém 501 testes.
- Arquivo final de aceite: **9 aprovados** (25,00 s); após fortalecer o cenário de autor repetido, esse caso foi executado novamente e passou.
- Rota de troca de origem na versão final: **20 aprovados** (49,93 s).
- Playwright focado com Chrome instalado: **6 aprovados** em desktop e 360 px (14,0 s). A primeira tentativa com Chromium padrão não iniciou porque o executável não estava instalado; repetir com `PLAYWRIGHT_CHANNEL=chrome` resolveu.
- Typecheck, build de produção e `git diff --check`: aprovados.

## Limites

- Um processo; trava e disponibilidade não são distribuídas.
- Origem confirmada não é revertida ao falhar a reconstrução. A resposta distingue alteração salva de reputação indisponível.
- Sem worker: dados corrompidos continuam indisponíveis até correção; novas consultas tentam recuperar.
- O serviço reconstrói a floresta e todos os eventos. Custo dos eventos O(E), mais leitura, ordenação O(N log N) e validação O(N) da floresta; sem vantagem assintótica de subárvore.
- A revisão independente exigida pela issue deve ocorrer no PR. Testes automatizados não substituem essa revisão.
