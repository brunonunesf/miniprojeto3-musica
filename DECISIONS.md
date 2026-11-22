# Decisões do time

**Time:** Bruno Nunes (@brunonunesf), Cecília Candeia (@cec1l14) e Daniel Dantas (@dnieldantas).

Documento inicial baseado nas mensagens de texto da conversa de WhatsApp. Ideias discutidas não significam funcionalidades prontas nem escopo fechado.

## Produto

- **Público inicial proposto:** ouvintes que descobrem músicas pelas indicações de amigos e outros ouvintes, com atenção à divulgação de artistas pequenos e independentes. O recorte mais específico ainda será validado pelo time.
- **Problema:** recomendações isoladas não mostram a corrente de descobertas nem reconhecem as pessoas que ajudaram uma música a chegar a novos ouvintes.
- **Como a rede resolve:** conectar reviews derivadas às suas origens e tornar visível a contribuição das pessoas por meio de árvores de recomendações e reputação.
- **Impacto pretendido:** incentivar a descoberta e a divulgação de artistas com menor visibilidade, como Daniel destacou na conversa.
- **Sinal de sucesso proposto, a validar:** pessoas descobrem uma música por outra pessoa e publicam uma review ligada à recomendação original.
- **Pendente de reunião (Etapa 1):** recorte específico do público (a rubrica valoriza algo como "estudantes da UFPB que querem descobrir artistas independentes locais" mais que "gente que gosta de música") e nome definitivo da rede. Enquanto isso, seed e interface usam o recorte provisório acima.

## Direções de produto registradas

### 1. Descoberta musical com origem visível

A referência inicial foi um “Letterboxd de músicas”. A conversa citou Music Board como concorrente e levantou a preocupação com diferenciação. A proposta posterior de Daniel acrescenta árvores de recomendações e reconhecimento de quem divulga. A comparação com concorrentes é um relato da conversa, não uma pesquisa verificada neste repositório.

### 2. Reviews derivadas criam conexões

Uma nova review vinculada à anterior cria uma conexão na árvore. Curtir apenas gera uma interação; não adiciona uma pessoa à árvore. Exemplo: Ana → Júlia → Pedro.

### 3. Reputação distribuída pela corrente

A proposta é que curtidas e novas recomendações gerem pontos, distribuídos também aos participantes anteriores, em parcelas menores conforme a distância. Pesos, profundidade máxima, tratamento de descurtidas, exclusões, repetições e prevenção de abuso continuam em aberto.

### 4. Nome e funcionalidades complementares em aberto

“MeetMusic” é placeholder: Daniel comentou que o nome já existe. Grupos de amigos, comparação semanal do que ouviram e mensagens diretas foram sugeridos, mas ainda não são compromisso de implementação. Um recorte exclusivamente paraibano foi levantado e considerado limitado; não foi adotado como restrição do produto.

## Funcionalidades e responsabilidades

Os itens de núcleo vêm da base oficial. Os demais são ideias da conversa; prioridade, escopo e donos serão definidos pelos três.

Divisão **sugerida**, baseada no guia 07 (time de 3), a ser confirmada pelos três. Pessoas A, B e C ainda não foram associadas a nomes.

| Pessoa | Área | Núcleo | Feature musical |
|---|---|---|---|
| A (Cecília) | Frontend | Auth, Perfil | Tela da árvore de recomendações |
| B (a confirmar) | Backend | Posts, Feed, Curtidas, Comentários | Review com nota e `origem_id` |
| C (a confirmar) | Dados | Follow, Seed fake | Reputação, estrutura em `core/` e deploy |

| Funcionalidade | Situação | Dono |
|---|---|---|
| Autenticação | Backend pronto na branch `feat/auth-bypass` (bypass `X-User-Id` com `DEBUG=true`, registro, login e `/auth/eu`), aguardando PR e revisão; telas de cadastro e login pendentes | A |
| Perfil | Núcleo a implementar | A |
| Posts, feed, curtidas e comentários | Núcleo a implementar conforme os testes da base | B |
| Follow | Núcleo a implementar | C |
| Seed de exemplo no nicho musical | Adaptar ao produto; fazer por último | C |
| Reviews (música + nota) e árvores de recomendações | Diferencial proposto | B (back), A (tela) |
| Reputação distribuída | Proposta; versão mínima abaixo | C |
| Bibliotecas de descobertas e recomendações | Ideia descrita por Daniel | A combinar |
| Grupos de amigos e conversa sobre a semana musical | Sugestão a avaliar | A combinar |
| Mensagens diretas | Sugestão a avaliar | A combinar |

## Escopo e cortes (proposta)

- **Entra:** núcleo oficial; review de música com nota (nota ainda é proposta); review derivada que aponta para a origem; visualização da árvore; reputação com pontuação decrescente por distância.
- **Fica de fora, salvo sobra de tempo:** bibliotecas pessoais, grupos, mensagens diretas e integração com streaming. Motivo: o prazo é 27/11 e o núcleo ainda não existe; um diferencial funcionando vale mais que várias ideias incompletas.

## Decisões técnicas propostas (a confirmar na reunião)

1. **Catálogo de músicas:** campos `titulo` e `artista` na própria review, sem API externa como requisito do núcleo. A identidade canônica ainda precisa ser definida para garantir unicidade por pessoa/música e correspondência futura entre serviços.
2. **Review como post:** a review é um post com campos extras (música, nota, `origem_id`), reaproveitando feed, curtidas e comentários.
3. **Reputação, versão mínima e provisória:** autor do post que recebeu a interação e seus dois ancestrais mais próximos, com pesos 1, 1/2 e 1/4 e profundidade máxima 3. Descurtidas, repetições e prevenção de abuso seguem em aberto.

## Escolhas técnicas pendentes

A stack inicial é a do esqueleto oficial: FastAPI + SQLAlchemy + SQLite e Next.js + TypeScript + Tailwind. A árvore de recomendações sugere explorar uma estrutura de árvores, mas nenhuma representação, algoritmo ou complexidade foi escolhida ou medida ainda.

Também faltam definir catálogo e identificação das músicas, eventual integração externa, regras para vincular reviews à origem e exibição das árvores. Foram aprovadas issues opcionais para investigar e implementar sugestões de reescuta via Spotify e Deezer; acesso e viabilidade ainda precisam ser validados. Não há compromisso de reprodução de áudio ou de entrega dessas integrações em 27/11.

A conversa menciona aplicação de ML, mas a proposta específica não está descrita nos textos disponíveis. Não se assume que reputação seja ML; a aplicação e sua exigência precisam ser confirmadas pelo time no material do curso.

## Organização e entrega

- O time decidirá a divisão das features e revisará as contribuições entre si.
- Após a preparação inicial, Bruno autorizou a criação das issues iniciais. Elas organizam o trabalho sem fechar o escopo: qualquer integrante com acesso pode abrir novas propostas. Responsáveis permanecem a combinar; nenhum PR de implementação foi criado.
- O guia oficial menciona GitHub Classroom. O convite não foi fornecido; confirmar o destino exigido para a entrega antes da submissão.

## Uso de IA

Codex foi usado para ler os textos exportados do WhatsApp, separar as ideias sobre música, consultar o material do miniprojeto e preparar o repositório e esta documentação. Não implementou funcionalidades da rede social, não transcreveu áudios e não definiu decisões de produto ausentes da conversa.

Codex também foi usado para organizar e abrir as issues iniciais com critérios de conclusão e dependências sugeridas, mantendo ideias opcionais separadas de compromissos de implementação.

Claude Code foi usado para analisar a pasta do projeto, propor o plano de etapas até a entrega e redigir as seções de donos, escopo e decisões técnicas propostas acima. Essas propostas estão sendo decididas pelo time.

Claude Code também implementou o backend da autenticação do núcleo (bypass `X-User-Id`, registro, login, `/auth/eu`, model de sessão) e atualizou o seed com os usuários `ana`, `bruno` e `carlos`. A implementação segue o guia 01 e foi verificada com `make test` (7 passed, 7 skipped). O código ainda precisa ser revisado por uma pessoa do time.

## Decisões confirmadas com Bruno — 21/11/2026

Estas definições complementam a discussão do time e orientam as issues; não indicam funcionalidades já implementadas. As propostas de responsáveis e pesos acima permanecem propostas, sem confirmação adicional nesta atualização.

| Tema | Decisão |
|---|---|
| Público | Descoberta entre amigos, permitindo qualquer música e dando atenção a artistas menores. O time pode refinar o recorte. |
| Review | Uma por pessoa/música, com texto editável; nova recomendação derivada exige review própria. |
| Origem | Raiz não tem origem; cada derivada tem exatamente uma. É permitido corrigir a origem para outra review da mesma música sem criar ciclos, preservando os descendentes. |
| Reputação após correção | Recalcular também as interações antigas conforme a árvore atual; créditos podem aumentar ou diminuir. A fórmula final permanece pendente. |
| Reescuta | Aviso separado no feed com comentário opcional; uma publicação por pessoa/música a cada intervalo móvel de 24 horas. |
| Histórico dos avisos | Avisos mantêm sua data/comentário e apontam para a análise atual, identificada como editada quando aplicável. |
| Efeito do aviso | Não cria nova review, nó ou pontos; curtidas e novas recomendações se vinculam à review original. |
| Streaming | Integrações opcionais sugerem reescutas, sempre confirmadas pelo usuário antes de publicar; registro manual continua disponível. |

Jornada: Ana recomenda → Júlia escreve review derivada → Júlia volta a ouvir e publica um aviso com comentário → outra pessoa abre a review de Júlia e continua a corrente. Se Júlia corrigir sua origem, seus descendentes permanecem ligados a ela e os créditos antigos são recalculados.

### Issues derivadas

- [#18 — Registrar e publicar reescutas](https://github.com/brunonunesf/miniprojeto3-musica/issues/18).
- [#19 — Corrigir origem](https://github.com/brunonunesf/miniprojeto3-musica/issues/19).
- [#20 — Recalcular reputação](https://github.com/brunonunesf/miniprojeto3-musica/issues/20).
- [#21 — Spotify](https://github.com/brunonunesf/miniprojeto3-musica/issues/21).
- [#22 — Deezer](https://github.com/brunonunesf/miniprojeto3-musica/issues/22).

Integrações e novas evoluções não viram automaticamente compromisso para 27/11. A validação de acesso ao Deezer é uma condição de viabilidade; caso bloqueada, a sincronização permanece pendente.

Continuam em aberto: identidade canônica da música, fórmula final, exclusões e efeito sobre avisos/árvores, auto-interações, visibilidade das bibliotecas, conversão de raiz em derivada ou remoção de origem, exigência de ML e destino Classroom. A edição aprovada não decide trocar a música da review.

Codex atualizou documentação e issues para registrar estas decisões, preservando as propostas e contribuições recentes do time. Nenhuma funcionalidade foi implementada nesta atualização.

## Regras adicionais confirmadas com Bruno — 21/11/2026

- **Versões de música:** gravação original, remix e versão ao vivo são itens musicais distintos, pois podem suscitar análises diferentes. A unicidade de uma review por pessoa se aplica a cada versão identificada. A chave técnica e o tratamento de edições/remasterizações ainda precisam ser definidos.
- **Descurtida:** ao desfazer uma curtida, os pontos que aquela curtida concedeu devem ser retirados. O valor exato segue pendente da fórmula.
- **Auto-interação:** uma curtida na própria review pode dar uma recompensa pequena. O número exato e a ausência ou presença de propagação aos ancestrais ainda precisam ser acordados.
- **Exclusão:** avisos de reescuta ligados a uma review excluída devem ser apagados. Reviews feitas por outras pessoas a partir dela devem permanecer. A forma de preservar a árvore e recalcular ou conservar reputação exige decisão adicional.
- **Bibliotecas:** cada pessoa deve poder escolher se sua biblioteca fica pública ou privada, por meio de controle explícito. A ação que registra uma descoberta e o comportamento ao trocar a visibilidade ainda precisam ser especificados.
- **Prazo de 27/11:** o objetivo do time é entregar o máximo que for viável, ajustando o escopo ao andamento. Isso não aprova automaticamente todas as ideias opcionais nem elimina a necessidade de demonstrar os fluxos que forem anunciados como prontos.

A fórmula de reputação e o destino dos descendentes/créditos na exclusão estão sendo discutidos; nenhuma opção apresentada pelo Codex deve ser tratada como decisão antes da resposta do time.
