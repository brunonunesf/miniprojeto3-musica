# Feed e descoberta musical — 25/11/2026

Planejamento aprovado por Bruno a partir das mensagens e imagens de 25/11 e das confirmações no chat. A imagem abaixo foi aprovada como referência visual, aberta a melhorias. É uma proposta: não comprova funcionalidades implementadas.

![Rascunho aprovado: perfil, feed e descoberta](planejamento/feed-descoberta-rascunho.png)

Capas, fotos, autores representados visualmente e contagens são ilustrativos; a imagem foi gerada por IA. Não usar essas fotos como identidade real dos integrantes, nem importar os números para produção. Texto da conversa e imagens foram examinados; áudios não foram transcritos. O histórico privado não integra este repositório.

## Experiência e layout

- Preservar fundo claro, cartões brancos arredondados, laranja #f58220, links #ad4c00 e Merriweather do frontend existente. Letterboxd orienta as vitrines de capas.
- A partir de 1024 px: perfil/navegação à esquerda, feed principal no centro, pesquisa/populares à direita. Abaixo disso: navegação compacta e acesso a /musicas; feed permanece principal. Sem rolagem horizontal da página a 360 px.
- Feed: reviews dos seguidos em ordem cronológica; não misturar sugestões ou incluir posts próprios automaticamente. Autor, data, capa, faixa, artista, versão, nota e acesso ao detalhe. O texto completo continua no detalhe; preservar indicação “Tem análise”/“Só nota”.
- Ações: curtir, comentar, escrever review derivada e compartilhar link. Usar o rótulo explícito “Escrever review a partir desta”; “Criar review derivada” na imagem é apenas abreviação visual. Compartilhamento nativo quando disponível, copiar link como alternativa; cancelamento não é falha de publicação.
- Derivar abre formulário com música e origem preenchidas. Respeitar uma review ativa por pessoa/gravação: se já existe, oferecer acesso à atual, sem duplicar nem trocar origem silenciosamente. Regras de opinião própria, origem única, mesma música, ciclos e exclusão continuam nas #1/#10/#33/#42.
- Mostrar origem e acesso à árvore quando disponíveis. A mudança de layout não dispensa validação/transação do backend. Reescuta continua ação distinta (#12/#45), sem criar nó ou pontuar sozinha.
- “Mais avaliadas na comunidade”: número de reviews públicas ativas por gravação, em todo o período. Não é popularidade no Spotify nem contagem de escutas. Curtir, editar e reescutar não aumentam esse número; excluir review reduz. Excluir gravações sem reviews.
- Busca por título/artista; clicar em capa abre página da música e suas reviews. Capas ausentes usam fallback existente.
- Descobrir continua personalizado, separado do feed e do ranking. Acesso lateral pode apontar para sua tela; não exige duplicar o recomendador no feed.
- Sem adição de bloqueio, ocultação, streaming, grupos, mensagens ou vitrines de amigos nesta mudança. Bibliotecas seguem seu planejamento próprio; o desenho não as torna entregues.

## Contratos para integração

| Interface | Comportamento |
|---|---|
| GET /feed?offset=0&limit=10 | items/total dos seguidos; created_at decrescente e ID decrescente; preservar contrato do núcleo. |
| GET /musicas?q=&offset=0&limit=10 | Reutilizar busca autenticada do #60, por título/artista. |
| GET /musicas/populares?offset=0&limit=10 | Autenticado; items/total; metadados musicais existentes + quantidade_reviews; quantidade decrescente, ID crescente. Rota fixa antes da dinâmica. |
| GET /musicas/{id}/reviews?offset=0&limit=10 | Autenticado; items/total; reviews públicas ativas no formato existente; created_at decrescente, ID decrescente. |
| /musicas e /musicas/{id} | Rotas frontend para pesquisa/populares e detalhe da gravação. |

Reutilizar limites/erros de paginação do catálogo; total representa o conjunto filtrado antes da paginação. Música inexistente: 404; sem sessão válida: 401. Paginação por offset pode mudar com novas interações, sem promessa de snapshot. No front, deduplicar IDs, reiniciar offset ao atualizar/trocar busca, descartar respostas antigas e preservar itens carregados em falhas de próxima página. Falha na lateral não bloqueia o feed. O contrato de nota/review do backend existente não é alterado por este planejamento.

## Entregas e responsabilidades

| Pessoa | Entrega | Acompanhamento |
|---|---|---|
| Cecília | Layout e ações do feed; aproveitar PRs #58/#63 | #36 |
| Cecília | Entrada de review derivada e review já existente | #33 |
| Daniel | Preservar feed cronológico e ações existentes | #6 |
| Daniel / Cecília | Origem, validação e árvore, cada qual em sua área | #10 / #42 |
| Daniel | Populares e listagem de reviews por música | #65 |
| Cecília | Pesquisa, populares e página da música | #66 |
| Bruno | Massa reproduzível para ranking/busca | #13 |
| Daniel / Bruno / Cecília | Personalização permanece separada | #23 / #55 / #56 |

Contagem no banco é backend, não exige novo algoritmo de ML. Responsáveis existentes e entregas em revisão são preservados. Cada issue conclui somente os critérios de sua área; documento e mocks não encerram implementação.

## Ordem e aceite

1. Publicar contratos e referência visual. Catálogo #32 precede integração de reviews #60; aproveitar #57/#58/#63 e revisar dependências atuais antes de integrar.
2. Backend e frontend podem avançar em paralelo com mocks identificados. Integrar catálogo, reviews, follow e feed antes de validar o fluxo completo.
3. Validar ranking com empates, exclusão, edição, reescuta, zero reviews e versões distintas; pesquisa e paginação; nenhum dado de biblioteca privada é exposto.
4. Validar feed só dos seguidos, detalhes, curtida/comentário, derivação com origem correta e duplicata recusada. Validar carregamento/vazio/erro, teclado, 360 px e desktop.
5. Executar testes relevantes de backend, TypeScript, build e testes de navegador; confirmar fluxo com API real e banco de demonstração separado. Resultados com mocks não comprovam persistência.
6. Para 27/11, priorizar núcleo funcional e navegação acordada. Árvores e Descobrir preservam prioridade anterior; opcionais ficam fora do caminho crítico. Mudanças futuras devem atualizar este documento e as issues.

## Origem e uso de IA

Codex inspecionou o frontend local, as issues e PRs do GitHub e as referências visuais. A ferramenta integrada de imagens gerou a prévia com o prompt: mockup desktop em português, identidade clara laranja/Merriweather, perfil à esquerda, reviews compactas ao centro, busca/populares à direita e Descobrir separado. Bruno aprovou a imagem e autorizou publicar e organizar o planejamento. Esta entrega altera documentação e organização do trabalho; não implementa a interface nem faz merge de PRs de código.
