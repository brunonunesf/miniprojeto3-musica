# Evidências de conclusão da entrega de dados — #13

Validação executada em 26/11/2026, em worktree e SQLite isolados. Dados musicais reais do catálogo aprovado; perfis, textos e interações fictícios. A interface recebeu respostas reais da API, sem mocks. Nenhum banco pessoal foi apagado.

## Critérios e comprovação

| Critério da #13 | Evidência |
|---|---|
| Seed completo | `test_seed_fake_popula_a_rede` ativo; 25 usuários, 20 músicas, 50 reviews, 20 follows, 30 curtidas e 3 origens persistidas. |
| Corrente, ramo e raiz independente | API e capturas: Bruno → Cecília → Daniel, Fernando no outro ramo, Gustavo em outra raiz de Clareou. Reinício coberto pela suíte. |
| Consistência e pontos | Motor #43 reconstruído de reviews/curtidas do banco, comparado com oráculo independente por chaves; resultados por usuário em `validacao.json`. Não é reputação exposta pelo perfil/API. |
| Reexecução preservando ações | Depois de editar, excluir, descurtir e deixar de seguir, a assinatura lógica permaneceu igual ao repetir o CLI. Estado do ensaio: 49 reviews, 19 follows, 28 curtidas e uma referência apagada. |
| Reset e recuperação | Reset recompôs 50/20/30; backup manteve o ensaio. O backup foi restaurado de verdade e a reexecução manteve o estado recuperado. Banco isolado foi deixado novamente no cenário inicial. |
| Ranking, busca e versões | 18 músicas avaliadas e duas sem reviews; contagens/empates conferidos pela API e pelos testes. Exclusão reduz contagem; edição não aumenta. Original/remix/ao vivo e homônimos usam fixtures técnicas separadas, sem misturar seis faixas fictícias no catálogo da demo. |
| Conta nova e conta com sinais | Ryan sem reviews/sinais e Bruno com reviews/interações reais da carga. Captura do perfil vazio e verificações de dados; personalização do Descobrir não é declarada entregue. |
| Preparação limpa | Ambiente novo via `uv sync --frozen`; catálogo/CLI, carga, repetição, startup/check, reset e restauração validados. |
| Testes e roteiro | `make test`: 378 passed, zero skips; `make check`, `make seed-validar`, TypeScript e diff-check aprovados. Roteiro em `docs/demo-issue-13.md`. |

## Capturas reais

- [Árvore em desktop](arvore-desktop.png).
- [Árvore em mobile, sem overflow horizontal](arvore-mobile.png).
- [Raiz independente](raiz-independente.png).
- [Ranking da comunidade](ranking.png).
- [Conta nova de Ryan](conta-nova.png).
- [Respostas, contagens e resultado de preservação/reset/recuperação](validacao.json).

O JSON não contém tokens, senhas nem hashes de senha. A assinatura SHA-256 é de um snapshot lógico de reviews/relações/referências, não de credenciais. IDs registrados são os retornados nessa execução, não um contrato fixo do aplicativo.

A inspeção das páginas não registrou erro de JavaScript nem resposta de API com status >=400 nas requisições capturadas. O backend respondeu 200 nas leituras/logins e 200/204 nas ações do ensaio; shutdown dos servidores concluído antes do reset e da recuperação.

## Limites e encerramento aprovado

Bruno escolheu concluir a entrega de dados sem aguardar todas as integrações de produto. Descobrir (#55/#23/#56), reputação persistida/exposta em API e preservação dos eventos históricos (#10), correção/recálculo e bibliotecas/reescutas (#12 e relacionadas) permanecem nas respectivas issues. Não foram implementados nesta entrega para simular conclusão dessas funcionalidades.

A reescuta não tem serviço integrado nesta base; por isso seu efeito na contagem não é apresentado como testado. A árvore após exclusão foi verificada pela API: referência apagada sem nome/nota/conteúdo, mantendo os descendentes.

Instruções de entrega conferidas no material versionado: `docs/README-base-trilha.md`, seção de datas, registra 27/11/2026. O README orienta confirmar eventual vínculo com GitHub Classroom, cujo convite não foi fornecido. Não houve envio institucional, acesso ao Classroom ou confirmação externa nesta validação.

## Uso de IA e reprodução

Codex revisou contratos, executou testes/CLI, gerou o relatório a partir do banco/API e capturou as telas com Playwright/Google Chrome. Nenhum texto fictício foi atribuído como opinião real dos participantes. O roteiro principal usa apenas comandos e contas documentados; para conferir os resultados exatos do ensaio, consultar `validacao.json`.
