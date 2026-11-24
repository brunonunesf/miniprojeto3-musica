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
| Autenticação | Backend integrado; front e reforços de autenticação implementados em `feat/issue-2-autenticacao`, aguardando revisão do time | A |
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
- **Prioridade para a demonstração de 27/11:** árvores de recomendações e área personalizada “Descobrir” (#23), após o núcleo necessário. Reputação entra com a fórmula básica 4/2/1; detalhes de interface e otimizações podem evoluir depois. O time tentará entregar o máximo viável conforme o andamento. Bibliotecas, grupos, mensagens diretas e integrações com streaming não são pré-requisitos das duas prioridades.

## Decisões técnicas propostas (a confirmar na reunião)

1. **Identificação das músicas:** a decisão de produto é distinguir cada faixa/versionamento selecionado. O modelo técnico deve guardar identificadores de serviço quando disponíveis e identificador local para entradas manuais; não presumir equivalência entre serviços apenas por título/artista.
2. **Review como post:** a review é um post com campos extras (música, nota, `origem_id`), reaproveitando feed, curtidas e comentários.
3. **Reputação:** a proposta anterior de pesos 1, 1/2 e 1/4 foi substituída pela decisão de 21/11/2026, descrita abaixo. A prevenção de abuso e o efeito de exclusões continuam em discussão.

## Escolhas técnicas pendentes

A stack inicial é a do esqueleto oficial: FastAPI + SQLAlchemy + SQLite e Next.js + TypeScript + Tailwind. A árvore de recomendações sugere explorar uma estrutura de árvores, mas nenhuma representação, algoritmo ou complexidade foi escolhida ou medida ainda.

O modelo técnico de catálogo, os identificadores externos e a interface das árvores serão definidos nas issues de implementação. Foram aprovadas issues opcionais para investigar e implementar sugestões de reescuta via Spotify e Deezer; acesso e viabilidade ainda precisam ser validados. Não há compromisso de reprodução de áudio ou de entrega dessas integrações em 27/11.

O time validou o uso de ML de forma simples na área “Descobrir” (#23): TF-IDF dos metadados musicais e similaridade de cosseno com preferências derivadas de curtidas e reviews. A rubrica disponível não menciona ML como exigência; eventual instrução adicional da organização pode ser acompanhada na entrega. Reputação por fórmula não é ML.

## Organização e entrega

- O time decidirá a divisão das features e revisará as contribuições entre si.
- Após a preparação inicial, Bruno autorizou a criação das issues iniciais. Elas organizam o trabalho sem fechar o escopo: qualquer integrante com acesso pode abrir novas propostas. Responsáveis permanecem a combinar; nenhum PR de implementação foi criado.
- O guia oficial menciona GitHub Classroom. O convite não foi fornecido; confirmar o destino exigido para a entrega antes da submissão.

## Uso de IA

Na preparação inicial, Codex foi usado para ler os textos exportados do WhatsApp, separar as ideias sobre música, consultar o material do miniprojeto e preparar o repositório e esta documentação. Naquela etapa, não implementou funcionalidades da rede social, não transcreveu áudios e não definiu decisões de produto ausentes da conversa.

Codex também foi usado para organizar e abrir as issues iniciais com critérios de conclusão e dependências sugeridas, mantendo ideias opcionais separadas de compromissos de implementação.

Claude Code foi usado para analisar a pasta do projeto, propor o plano de etapas até a entrega e redigir as seções de donos, escopo e decisões técnicas propostas acima. Essas propostas estão sendo decididas pelo time.

Claude Code também implementou o backend da autenticação do núcleo (bypass `X-User-Id`, registro, login, `/auth/eu`, model de sessão) e atualizou o seed com os usuários `ana`, `bruno` e `carlos`. A implementação segue o guia 01 e foi verificada com `make test` (7 passed, 7 skipped). O código ainda precisa ser revisado por uma pessoa do time.

## Decisões de produto validadas pelo trio — 22/11/2026

Bruno informou que Cecília e Daniel revisaram e validaram as decisões de produto discutidas. O nome “MeetMusic” permanece provisório; escolher outro nome não bloqueia as funcionalidades.

| Tema | Regra aprovada |
|---|---|
| Público | Descoberta de músicas entre amigos, com espaço para artistas menores. |
| Identidade da música | Cada faixa/versionamento selecionado no aplicativo de música é um item próprio: gravação original, remix e versão ao vivo podem receber reviews diferentes. Quando uma faixa vier de Spotify ou Deezer, guardar identificador do serviço; para entrada local, usar identificador interno. Relacionar faixas de serviços diferentes somente após confirmar que representam a mesma gravação. |
| Review | Uma review ativa e editável por pessoa e item musical. Nova recomendação derivada exige texto próprio e uma única origem. Raiz não tem origem. |
| Descoberta | Publicar uma review derivada registra na biblioteca que a música foi descoberta a partir daquela origem. Publicar uma review independente registra recomendação própria, sem afirmar descoberta por outra pessoa. Visitar ou curtir não registra escuta. |
| Origem | O autor pode corrigir para outra review da mesma música sem criar ciclos; descendentes permanecem. Corrigir a origem recalcula pontos antigos e futuros. |
| Reescuta | Aviso separado no feed com comentário opcional, no máximo um por pessoa/música a cada 24 horas; aponta para a review atual, mas preserva data e comentário do aviso. Não cria nó nem pontua. |
| Bibliotecas | Controles separados. Descobertas começam privadas e recomendações públicas; o dono pode alternar. Terceiros veem aviso de acesso restrito para lista privada, sem itens, contagem ou origens. Reviews públicas seguem visíveis. |
| Prioridade | Para 27/11, tentar entregar o máximo viável, com árvores e área “Descobrir” (#23) como diferenciais de demonstração e reputação 4/2/1 básica. |
| ML | Escolha de produto: recomendar faixas e reviews em “Descobrir” com TF-IDF e similaridade, usando curtidas e reviews como sinais. O material disponível não afirma que ML é obrigação do curso. |
| Classroom | Não é condição para fechar esta decisão; o time usará o repositório atual como trabalho útil e seguirá as instruções de entrega que receber. |

**Decisão adiada:** transformar uma raiz em derivada ou remover a origem de uma derivada. A primeira versão permite corrigir uma origem já existente; ampliar esse fluxo exige regra e teste próprios. Spotify e Deezer continuam integrações opcionais para sugerir reescutas confirmadas pelo usuário.

**Exemplo de corrente:** Ana recomenda; Júlia publica uma review derivada da de Ana; Pedro publica outra a partir da de Júlia. Uma segunda pessoa pode publicar a partir da review de Ana, formando outro ramo. Cada review derivada tem uma origem, e curtidas não acrescentam nós.

### Issues relacionadas

- [#9 — Música e review](https://github.com/brunonunesf/miniprojeto3-musica/issues/9); [#10 — Árvore](https://github.com/brunonunesf/miniprojeto3-musica/issues/10); [#11 — Reputação](https://github.com/brunonunesf/miniprojeto3-musica/issues/11); [#12 — Bibliotecas](https://github.com/brunonunesf/miniprojeto3-musica/issues/12).
- [#18 — Reescutas](https://github.com/brunonunesf/miniprojeto3-musica/issues/18); [#19 — Correção de origem](https://github.com/brunonunesf/miniprojeto3-musica/issues/19); [#20 — Recálculo](https://github.com/brunonunesf/miniprojeto3-musica/issues/20); [#23 — Descobrir](https://github.com/brunonunesf/miniprojeto3-musica/issues/23).
- [#21 — Spotify](https://github.com/brunonunesf/miniprojeto3-musica/issues/21) e [#22 — Deezer](https://github.com/brunonunesf/miniprojeto3-musica/issues/22) são opcionais.

## Fórmula e exclusão confirmadas com Bruno — 21/11/2026

- **Curtida de outra pessoa em uma review:** o autor recebe 4 pontos, o autor da review de origem imediata recebe 2 e o ancestral seguinte recebe 1. Níveis anteriores não recebem. O evento de curtida é único por usuário/review; descurtir retira exatamente os pontos que ele concedeu. Recurtir após descurtir volta a conceder uma única vez.
- **Review derivada:** sua publicação gera 4 pontos para o autor da origem imediata, 2 para o ancestral seguinte e 1 para o próximo ancestral. O autor da nova review não recebe pontos por esse evento. Cada review derivada gera esse evento uma única vez; alterar a origem recalcula os créditos existentes segundo a árvore corrigida, sem criar um novo evento.
- **Curtida própria:** concede 1 ponto somente ao autor da review, sem propagar para ancestrais; descurtir remove esse ponto. A regra de unicidade também se aplica.
- **Exemplo:** Ana → Júlia → Pedro. Uma curtida externa na review de Pedro dá 4 a Pedro, 2 a Júlia e 1 a Ana. Publicar a review de Pedro dá 4 a Júlia e 2 a Ana; não há terceiro ancestral nesse caminho. Uma curtida de Pedro na própria review dá 1 somente a Pedro.
- **Exclusão:** excluir a review de Ana remove seu conteúdo e seus avisos de reescuta. A review de Júlia e as demais descendentes permanecem ligadas a um registro de origem apagada. O link para a review apagada abre uma página que informa que ela não existe mais, sem mostrar a análise. Mesmo após a exclusão, Ana conserva o crédito de origem: interações futuras com reviews descendentes continuam percorrendo o registro apagado e podem pontuar Ana conforme a fórmula. Ana pode publicar uma nova review da mesma música, como outra raiz, sem ligação automática com a antiga. A nova review não recupera o texto ou os avisos anteriores.

A fórmula usa pontos inteiros, sem arredondamento. Caso o mesmo autor apareça em mais de um nível do mesmo evento, recebe somente sua maior parcela. O recálculo após edição de origem aplica a mesma regra.

## Descobrir para você — prioridade de demonstração

- **Local:** área própria “Descobrir”, separada do feed cronológico de pessoas seguidas.
- **Sinais:** músicas analisadas e curtidas pela pessoa; review própria pesa 3 e curtida em review de outra pessoa pesa 1. Curtida própria não duplica o sinal da review.
- **Dados:** gêneros, tags e artista associados a cada identidade musical. Não usar texto de review como aprovação automática. Original, remix e versão ao vivo são identidades distintas.
- **Método inicial:** TF-IDF aprendido do catálogo local e similaridade de cosseno com o perfil de gosto. Não requer áudio, API de streaming ou treinamento supervisionado. É um recomendador simples; sua qualidade depende do catálogo e das interações disponíveis.
- **Saída:** reviews públicas e ativas de músicas ainda não analisadas, uma por identidade musical, com motivo curto baseado em características compartilhadas. Sem sinais, exibir reviews recentes e variadas e explicar que a personalização começará com interações.
- **Prioridade:** junto às árvores, é um dos dois diferenciais pretendidos para a demonstração de 27/11. Reputação básica permanece no escopo planejado; a implementação real será ajustada conforme o andamento.

Implementação e validação estão na [issue #23](https://github.com/brunonunesf/miniprojeto3-musica/issues/23). O material consultado não confirma obrigação de ML. O guia de setup cita GitHub Classroom, mas o convite não está disponível; a decisão do produto não depende dele.


## Implementação da autenticação — issue #2 — 24/11/2026

- A base local já continha o backend de autenticação integrado em `main`; a referência anterior a backend ainda isolado em branch estava desatualizada. A conclusão do front foi implementada em `feat/issue-2-autenticacao`, sem alterar branches do time.
- Escolhas confirmadas por Bruno no planejamento: identidade musical leve, fundo claro, destaque violeta e entrada automática após cadastro. O nome definitivo da rede continua em aberto. Sem novas bibliotecas de componentes ou fontes externas.
- Sessão centralizada em um provedor de contexto com verificação no carregamento. O token opaco permanece em `localStorage`, conforme o guia 01, e o cliente de API envia Bearer. Página inicial e usuários só são montados após validação de `/auth/eu`; a guarda visual não substitui autorização no backend.
- Resposta 401 de chamada autenticada limpa o estado e redireciona para login. Erros de rede/servidor preservam o token e permitem repetir a verificação. Respostas antigas não devem invalidar um token já substituído. A saída se propaga entre abas.
- Logout é local, sem revogação no servidor ou expiração de tokens. Recuperação de senha, e-mail, login social, JWT e cookies ficam fora desta entrega. Não há mudança de esquema, migração ou exclusão de dados.
- Senhas aceitam mínimo de 8 caracteres e máximo de 72 bytes UTF-8, validado antes do bcrypt. Não há truncamento. Hash vazio/inválido recebe 401 genérico; colisão de username na gravação recebe 409 após rollback. Sessão sem usuário recebe 401.
- O cadastro usa `/auth/registro`, seguido de `/auth/login`. Se o segundo passo falhar, a conta permanece criada e a interface encaminha ao login com confirmação e usuário preenchido. `/usuarios` mantém o slice de exemplo sem senha e não substitui o cadastro.
- Foi encontrado o PR #24 de Cecília (`feat/telas-auth`), que também implementa autenticação e propõe paleta quente. Esta branch é uma implementação alternativa do plano aprovado neste chat, não uma alteração daquele PR. O time precisa conciliar as duas propostas antes de integrar; os PRs de perfil e página inicial também podem se sobrepor ao layout. Nenhum merge foi realizado automaticamente.
- Codex implementou formulários, provedor de sessão, navegação, guarda, tratamento de erros, ajustes no backend e testes. A revisão por outra pessoa continua pendente.
- Verificação: 26 testes de backend passaram; 7 testes de outras features seguem pendentes. Build de produção e TypeScript passaram. Os 12 testes de navegador passaram com Google Chrome em desktop e largura de 360 px, incluindo cadastro, login, refresh, Bearer, token inválido, erro 500, conexão interrompida, saída entre abas e teclado. Capturas de login e registro foram inspecionadas visualmente. `make check` passou com banco separado em `/tmp`, sem alterar dados locais.
