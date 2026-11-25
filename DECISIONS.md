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

Os itens de núcleo vêm da base oficial. As prioridades e decisões de produto continuam sendo do trio; a divisão de áreas foi confirmada por Bruno em 24/11/2026.

| Pessoa | Área | Responsabilidades |
|---|---|---|
| Cecília (@cec1l14) | Frontend (`front`) | Telas, componentes, navegação e integração da interface com a API. |
| Daniel (@dnieldantas) | Backend (`back`) | APIs, persistência, permissões e integrações externas. |
| Bruno (@brunonunesf) | Dados e machine learning (`dados`) | Seed, catálogo, estruturas de dados, algoritmos de reputação e recomendador com sua validação. |

Uma funcionalidade pode envolver várias áreas. As etiquetas indicam participação, não exclusividade: o simples uso do banco é backend e não exige `dados`. Os responsáveis já atribuídos no GitHub e as contribuições anteriores são preservados. A autenticação (#2), concluída com participação de Bruno, não será redistribuída retroativamente.

| Funcionalidade | Participação por área |
|---|---|
| Autenticação (#2) | Cecília: front; Daniel: back nas manutenções futuras. Preservado o histórico de implementação de Bruno e do time. |
| Perfil, posts, follow, feed, curtidas e comentários (#3–#8) | Cecília: front; Daniel: back. |
| Músicas e reviews (#9) | Cecília: interface; Daniel: modelo persistido e API; Bruno: catálogo, gêneros, tags e consistência das identidades musicais. |
| Árvores de recomendações (#10) | Cecília: visualização; Daniel: persistência e API; Bruno: estrutura e algoritmos de percurso e prevenção de ciclos. |
| Reputação (#11) e recálculo (#20) | Bruno: cálculo e validação; Daniel: eventos, persistência e API; Cecília: exibição e feedback. |
| Bibliotecas (#12) | Cecília: telas; Daniel: consultas e autorização. |
| Seed e demonstração (#13) | Bruno: dados fictícios, cenários e validação do seed; roteiro e apresentação continuam coletivos. |
| Grupos e mensagens (#14–#15) | Avaliação coletiva; Cecília avalia a experiência e Daniel a viabilidade do backend. Implementação depende da decisão de produto. |
| Reescutas (#18) | Cecília: interface; Daniel: registros, permissões e limite de 24 horas. |
| Correção de origem (#19) | Cecília: confirmação e feedback; Daniel: alteração persistida e integração; Bruno: validação da árvore e integração com o recálculo. |
| Spotify e Deezer (#21–#22) | Daniel: viabilidade, autorização e API; Cecília: conexão e confirmação na interface. Integrações opcionais. |
| Descobrir (#23) | Bruno: recomendador TF-IDF, similaridade e validação; Daniel: endpoint e integração; Cecília: tela e explicação das sugestões. |

A divisão organiza o trabalho futuro e não altera o estado de conclusão das funcionalidades. Os registros de andamento e implementação nas demais seções são históricos e devem ser lidos com suas datas.

## Escopo e cortes (proposta)

- **Entra:** núcleo oficial; review de música com nota (nota ainda é proposta); review derivada que aponta para a origem; visualização da árvore; reputação com pontuação decrescente por distância.
- **Prioridade para a demonstração de 27/11:** árvores de recomendações e área personalizada “Descobrir” (#23), após o núcleo necessário. Reputação entra com a fórmula básica 4/2/1; detalhes de interface e otimizações podem evoluir depois. O time tentará entregar o máximo viável conforme o andamento. Bibliotecas, grupos, mensagens diretas e integrações com streaming não são pré-requisitos das duas prioridades.

## Decisões técnicas propostas (a confirmar na reunião)

1. **Identificação das músicas:** a decisão de produto é distinguir cada faixa/versionamento selecionado. O modelo técnico deve guardar identificadores de serviço quando disponíveis e identificador local para entradas manuais; não presumir equivalência entre serviços apenas por título/artista.
2. **Review como post:** a review é um post com campos extras (música, nota, `origem_id`), reaproveitando feed, curtidas e comentários.
3. **Reputação:** a proposta anterior de pesos 1, 1/2 e 1/4 foi substituída pela decisão de 21/11/2026, descrita abaixo. A prevenção de abuso e o efeito de exclusões continuam em discussão.

## Decisões técnicas implementadas — autenticação (22/11/2026)

Seguem o guia 01 e estão na `main`. Dos 10 testes do núcleo, os 3 de autenticação passam. Além deles, `backend/tests/test_auth_casos.py` cobre os casos de borda da issue #2: cabeçalho inválido, token falso, login de usuário sem senha, resposta única de erro, ausência de senha e hash nas respostas, limites de senha e bypass com e sem `DEBUG`. Na versão da `main` de 22/11, `make test` mostrava 19 passed e 7 skipped; os 7 restantes (posts, feed, perfil, follow, curtidas, comentários e seed) continuam por fazer.

- **Sessão por token opaco em tabela.** O login cria um token aleatório (`secrets.token_urlsafe(32)`) salvo na tabela `sessions`, enviado em `Authorization: Bearer <token>`. É mais simples de depurar e revogar que JWT, que o guia deixa como opcional.
- **Senha com hash bcrypt.** A senha nunca é guardada nem devolvida. Nesta branch, o registro valida no mínimo 8 caracteres e no máximo 72 bytes UTF-8 antes do bcrypt, sem truncamento. A contagem anterior somente por caracteres foi corrigida no PR #27.
- **Login com uma única resposta de erro.** Usuário inexistente, usuário sem senha e senha errada devolvem o mesmo `401`, para não revelar quais usernames existem. Username repetido no registro devolve `409`.
- **Bypass só em desenvolvimento.** O header `X-User-Id` só vale com `DEBUG=true`. Essa variável nunca deve ser ligada no deploy; sem ela só o token autentica.
- **Token no `localStorage` do navegador.** Foi escolhido por ser mais simples de entender e depurar. A troca por cookie `httpOnly` exigiria configurar CORS com credenciais, e o trade-off (XSS contra CSRF) está descrito no guia 01.
- **Forma de saída.** Sair apaga o token guardado no navegador, como o guia 01 descreve, e leva para `/login`. Não existe rota de logout no servidor: a sessão não é revogada e o token não expira, então um token copiado antes de sair continua válido. É uma limitação conhecida e aceita para este projeto; se o time decidir revogar, bastaria uma rota `POST /auth/logout` que apague a linha de `sessions` e, se necessário, uma data de validade na tabela.
- **A home exige login.** Nesta branch, o `AuthProvider` central valida `/auth/eu` antes de montar as páginas privadas. Quem implementar o feed em `app/page.tsx` deve manter a guarda central. Uma resposta `401` com token salvo apaga o token e volta para `/login`.
- **CORS só para `localhost:3000`.** O frontend precisa rodar nessa porta; em outra, o navegador bloqueia as chamadas e a interface mostra que não conseguiu falar com o backend.
- **Seed de desenvolvimento** com os usuários `ana`, `bruno` e `carlos`, todos com a mesma senha de desenvolvimento. Esses usuários e essa senha não devem existir no deploy.

## Proposta visual da branch `feat/telas-auth` (22/11/2026)

Proposta de Cecília, implementada na branch `feat/telas-auth` e sujeita à revisão do time, já que as cores afetam todas as páginas. Esta seção registra as escolhas daquele PR; a identidade aprovada por Bruno e aplicada no PR #27 está descrita ao final deste documento.

- **Tema escuro com neon.** Fundo quase-preto, cartões um tom acima e texto em branco suave. Magenta marca as ações, ciano marca foco e navegação, e o amarelo fica reservado para notas e pontos. O brilho aparece só no botão principal e no campo em foco, para o neon continuar sendo destaque.
- **Cores centralizadas.** Ficam em um único bloco `@theme` do `globals.css`; trocar a identidade custa mudar esses valores, não as telas.
- **Componentes reutilizáveis** em `frontend/components/`: `Botao`, `Cartao`, `Campo` e `MensagemErro`. As próximas telas devem usá-los para evitar repetir classes.
- **Títulos com fonte serifada.** Dão um tom editorial e combinam com o nicho de música.
- **Alternativa descartada:** uma paleta quente (creme e laranja), usada por pouco tempo. Foi trocada pelo tema escuro porque combina mais com o clima de show e de música.
- **Pendente:** nome definitivo da rede e logo. A navbar ainda mostra "Rede da Trilha".

## Escolhas técnicas pendentes

A stack inicial é a do esqueleto oficial: FastAPI + SQLAlchemy + SQLite e Next.js + TypeScript + Tailwind. A árvore de recomendações sugere explorar uma estrutura de árvores, mas nenhuma representação, algoritmo ou complexidade foi escolhida ou medida ainda.

O modelo técnico de catálogo, os identificadores externos e a interface das árvores serão definidos nas issues de implementação. Foram aprovadas issues opcionais para investigar e implementar sugestões de reescuta via Spotify e Deezer; acesso e viabilidade ainda precisam ser validados. Não há compromisso de reprodução de áudio ou de entrega dessas integrações em 27/11.

O time validou o uso de ML de forma simples na área “Descobrir” (#23): TF-IDF dos metadados musicais e similaridade de cosseno com preferências derivadas de curtidas e reviews. A rubrica disponível não menciona ML como exigência; eventual instrução adicional da organização pode ser acompanhada na entrega. Reputação por fórmula não é ML.

## Organização e entrega

- O time decidirá a divisão das features e revisará as contribuições entre si.
- Após a preparação inicial, Bruno autorizou a criação das issues iniciais. Elas organizam o trabalho sem fechar o escopo: qualquer integrante com acesso pode abrir novas propostas. Responsáveis das Pessoas B e C permanecem a combinar.
- Já foram abertos PRs: o #16 (backend de autenticação) e o #17 (documentação) estão mesclados, e o PR das telas de cadastro e login (`feat/telas-auth`) aguarda revisão. Os PRs mesclados até agora ainda não passaram por revisão de outra pessoa do time; os próximos devem passar.
- O guia oficial menciona GitHub Classroom. O convite não foi fornecido; confirmar o destino exigido para a entrega antes da submissão.

## Uso de IA

Na preparação inicial, Codex foi usado para ler os textos exportados do WhatsApp, separar as ideias sobre música, consultar o material do miniprojeto e preparar o repositório e esta documentação. Naquela etapa, não implementou funcionalidades da rede social, não transcreveu áudios e não definiu decisões de produto ausentes da conversa.

Codex também foi usado para organizar e abrir as issues iniciais com critérios de conclusão e dependências sugeridas, mantendo ideias opcionais separadas de compromissos de implementação.

Claude Code foi usado para analisar a pasta do projeto, propor o plano de etapas até a entrega e redigir as seções de donos, escopo e decisões técnicas propostas acima. Essas propostas estão sendo decididas pelo time.

Claude Code também implementou o backend da autenticação do núcleo (bypass `X-User-Id`, registro, login, `/auth/eu`, model de sessão) e atualizou o seed com os usuários `ana`, `bruno` e `carlos`. A implementação segue o guia 01 e foi verificada com `make test` (7 passed, 7 skipped). O código ainda precisa ser revisado por uma pessoa do time.

Claude Code também implementou o frontend da autenticação (páginas `/registro` e `/login`, token no `localStorage`, guarda de rota, botão de sair na navbar) e aplicou o tema visual escuro com neon, com os componentes reutilizáveis `Botao`, `Cartao`, `Campo` e `MensagemErro`. Foi verificado com `npx tsc --noEmit` e testado à mão no navegador (cadastro, login, erro de senha e sair). Também foi usado para diagnosticar problemas de ambiente (porta do frontend e CORS, processo preso na porta do backend e cache `.next`). O código e as cores ainda precisam ser revisados por uma pessoa do time.

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
- Escolhas finais aprovadas por Bruno: fundo claro, destaque laranja, Merriweather nos textos e alfabeto musical geométrico próprio no título do login. A entrada automática após cadastro foi mantida. A proposta inicial violeta foi substituída durante a revisão visual. O nome definitivo da rede continua em aberto; não foram adicionadas bibliotecas de componentes ou animação.
- Sessão centralizada em um provedor de contexto com verificação no carregamento. O token opaco permanece em `localStorage`, conforme o guia 01, e o cliente de API envia Bearer. Página inicial e usuários só são montados após validação de `/auth/eu`; a guarda visual não substitui autorização no backend.
- Resposta 401 de chamada autenticada limpa o estado e redireciona para login. Erros de rede/servidor preservam o token e permitem repetir a verificação. Respostas antigas não devem invalidar um token já substituído. A saída se propaga entre abas.
- Logout é local, sem revogação no servidor ou expiração de tokens. Recuperação de senha, e-mail, login social, JWT e cookies ficam fora desta entrega. Não há mudança de esquema, migração ou exclusão de dados.
- Senhas aceitam mínimo de 8 caracteres e máximo de 72 bytes UTF-8, validado antes do bcrypt. Não há truncamento. Hash vazio/inválido recebe 401 genérico; colisão de username na gravação recebe 409 após rollback. Sessão sem usuário recebe 401.
- O cadastro usa `/auth/registro`, seguido de `/auth/login`. Se o segundo passo falhar, a conta permanece criada e a interface encaminha ao login com confirmação e usuário preenchido. `/usuarios` mantém o slice de exemplo sem senha e não substitui o cadastro.
- Foi encontrado o PR #24 de Cecília (`feat/telas-auth`), que também implementa autenticação e tem proposta visual própria, descrita na seção de 22/11. Esta branch é uma implementação alternativa do plano aprovado neste chat, não uma alteração daquele PR. O time precisa conciliar as duas propostas antes de integrar; os PRs de perfil e página inicial também podem se sobrepor ao layout. Nenhum merge foi realizado automaticamente.
- Codex implementou formulários, provedor de sessão, navegação, guarda, tratamento de erros, ajustes no backend e testes. A revisão por outra pessoa continua pendente.
- Verificação: 26 testes de backend passaram; 7 testes de outras features seguem pendentes. Build de produção e TypeScript passaram. Os 12 testes de navegador passaram com Google Chrome em desktop e largura de 360 px, incluindo cadastro, login, refresh, Bearer, token inválido, erro 500, conexão interrompida, saída entre abas e teclado. Capturas de login e registro foram inspecionadas visualmente. `make check` passou com banco separado em `/tmp`, sem alterar dados locais.


## Identidade visual aprovada — 24/11/2026

- Bruno aprovou o laranja claro `#f58220`, hover `#e67412`, texto de destaque `#ad4c00` e texto escuro dos botões `#431d08`. Os contrastes calculados dos botões normal/hover são 5,71:1 e 4,85:1; links sobre branco têm 5,51:1.
- Merriweather é carregada por `next/font/google`, servida localmente após o build. Login e página após entrar adotam composição de capa de álbum: arte à esquerda e conteúdo à direita, empilhados abaixo de 900 px. Cadastro e usuários preservam sua largura.
- Após rejeitar os primeiros adornos sobre letras da Merriweather, Bruno aprovou 52 desenhos geométricos próprios: maiúsculas e minúsculas construídas com hastes, barras e cabeças de notas. As pranchas e a amostra aprovadas estão em `docs/identidade/`; os dados reutilizáveis dos 52 glifos, espaço, pontuação e acentos da frase estão em `frontend/components/music-glyphs.json`.
- O título “Novas músicas, novas conexões.” usa os vetores aprovados, sem substituir a fonte dos formulários. O lettering é desenho SVG, não uma fonte TTF/WOFF instalada. Os contornos anteriores derivados da Merriweather foram removidos.
- A entrada revela as duas linhas continuamente em aproximadamente 4 segundos, sem efeito de digitação. Pautas ondulam em ciclo de 18 segundos; notas flutuam em ciclos de 12–20 segundos. O botão pausa/retoma as animações. A preferência de movimento reduzido mostra o título completo e o fundo parado. A interação com o formulário não reinicia a entrada.
- A home saúda o usuário autenticado, oferece o acesso real a `/usuarios` e informa que o feed está em preparação. Não inclui posts, contagens ou interações fictícias. As regras de autenticação e o banco permanecem inalterados nesta revisão visual.
- Codex criou os componentes, as animações e os desenhos vetoriais a partir das orientações e da referência visual fornecida por Bruno. As pranchas foram aprovadas antes da aplicação. Não foi usado um novo pacote de fontes ou animação.
- Validação visual e de comportamento em 1440, 1024, 768 e 360 px: ausência de cortes nos glifos/rolagem horizontal, pausa/retomada, movimento reduzido, nomes longos e ausência de reinício ao digitar. Build de produção e TypeScript passaram. As suítes de backend e navegador são registradas no PR com os resultados finais.

- Na preparação do PR #27, as atualizações recentes de `origin/main` foram incorporadas sem reescrever o histórico: preservados os testes adicionais `test_auth_casos.py`, a documentação de Cecília e o registro das propostas visuais em revisão. O conflito na tabela de andamento foi conciliado para mencionar os dois PRs.
- Verificação final após conciliar a `main`: **38 testes de backend passaram**, com 7 pendentes de outras features; **12 testes de navegador passaram** em desktop e celular. TypeScript e o build da versão final passaram; os testes de navegador usaram os servidores locais de prévia com SQLite separado dos dados de desenvolvimento.

## Posts e reviews — issues #3 e #9 — 25/11/2026

Inspirado no Letterboxd, o post da rede **é uma review de uma música do catálogo**: a música e a nota são obrigatórias e o texto é opcional. Uma review pode ser só a nota. A pessoa **escolhe** a música em um catálogo curado; não digita uma música nova.

- **Rotas de posts:** `POST /posts` (201), `GET /posts/{id}`, `PATCH /posts/{id}` e `DELETE /posts/{id}` (204). Todas exigem login.
- **Corpo de `POST /posts`:** `{"musica_id": int, "nota": 0 a 10, "texto"?}`. Esta é uma **evolução do contrato do núcleo**, que aceitava só `texto`; o `test_posts_crud` foi adaptado sem remover nenhuma verificação. Os testes ainda `@skip` de feed, curtidas, comentários e perfil usam o formato antigo e serão adaptados quando cada feature for implementada. Um `musica_id` fora do catálogo devolve `422`.
- **Resposta:** `id`, `texto`, `tem_texto`, `nota`, `musica` (todos os dados do catálogo), `autor` (usuário completo) e `created_at`.
- **Rotas do catálogo:** `GET /musicas?q=&offset=&limit=` (busca por termos de título e artista, sem diferença de caixa, paginada, limite de 1 a 100) e `GET /musicas/{id}`. Exigem login. Não há cadastro de música pela API.
- **Catálogo:** o backend importa `backend/data/musicas.json` (entrega de dados do Bruno, #32) a cada subida, de forma idempotente: a chave curada `chave_catalogo` identifica a gravação e o `id` do banco é atribuído uma vez e preservado. Um catálogo inválido impede a subida, em vez de gravar parte dele. A busca ignora caixa e acentos ("mare" encontra "Maré"); ela filtra em Python, porque o SQLite não faz essa comparação Unicode, e custa O(n) por consulta, o que é aceitável para um catálogo curado pequeno.
- **Identidade da música:** a chave curada é a identidade; título e artista iguais não unem gravações. Original, remix, ao vivo e remaster são músicas distintas e recebem reviews distintas.
- **Nota:** inteira de 0 a 10, obrigatória e editável. Escala provisória, aprovada "por enquanto"; meia nota ou estrelas podem vir depois. Nota fora do intervalo ou decimal devolve `422`.
- **Texto:** opcional, até 5000 caracteres, com espaços das pontas removidos. O limite é generoso, na linha do Letterboxd, porque o feed mostra só o indicador e o texto completo aparece apenas no detalhe; ele existe para proteger a API e o banco. O valor foi proposto por Daniel e a #3 pede que o time o confirme. Quando houver review derivada (#10), o DECISIONS.md já exige texto próprio nela.
- **Forma da review no feed (proposta de Daniel, a confirmar com Bruno e Cecília):** cartão compacto com a **capa**, o **nome da música** e a **nota**, mais um **indicador de que existe texto** (`tem_texto`); clicar na review abre o detalhe com o texto completo. Ainda não foi combinada com o time. A tela do feed (#36, PR #58) tem uma primeira versão de Cecília com elementos parecidos, e a disposição final é dela.
- **Capa:** a música tem `capa_url` opcional, hoje vazia, porque o catálogo ainda não traz esse campo. Quando o Bruno o incluir nos dados, a importação o grava sem mudança no backend. Enquanto isso, a interface mostra uma imagem substituta.
- **Uma review por pessoa e versão.** Uma segunda review da mesma versão pelo mesmo autor devolve `409`, inclusive em envios simultâneos, porque a decisão é da restrição única do banco e não de uma consulta prévia; apagar a review libera uma nova. A oferta de edição ou reescuta fica para a #18.
- **A música não muda na edição.** `PATCH` altera só nota e texto, e um `musica_id` enviado ali é ignorado; trocar a música de uma review é decisão pendente da #9.
- **Ids absurdos:** um id maior que o inteiro do banco (`musica_id` no corpo, ou `post_id` e `musica_id` na rota) devolve `422`, e não um erro `500`. Foi apontado na revisão da Cecília.
- **Autoria vem da sessão.** Um `autor_id` enviado pelo cliente é ignorado. Editar ou excluir review de outra pessoa devolve `403` sem alterar o banco; review inexistente devolve `404`, verificado antes da permissão.
- **Preparação da árvore:** `origem_id` ainda não existe. Será uma coluna opcional do `Post` na #10, sem quebrar o contrato acima.
- **Exclusão:** por enquanto apaga a review. A política para descendentes de uma review excluída será definida junto com a #10.
- **Esquema do banco:** as tabelas `posts` e `musicas` são novas. Quem já tem um `backend/app.db` antigo precisa recriá-lo com `rm backend/app.db && make seed`, porque o `create_all` não altera tabelas existentes.
- Claude Code implementou o CRUD de reviews, a importação e as rotas do catálogo e seus testes (`test_posts_crud`, `test_posts.py` e `test_musicas.py`). Foi verificado com `make test` (75 passed, 6 skipped). O código ainda precisa ser revisado por outra pessoa do time.

## Perfil — conciliação com a identidade aprovada (25/11/2026)

- As telas de perfil passaram a usar o visual e a sessão central do PR #27. Os componentes do tema escuro (`feat/telas-auth`) foram removidos.
- `eu` e `stats` são usernames reservados, porque colidem com rotas fixas de `/usuarios`.
- Cada perfil recria o componente e descarta respostas de um perfil já abandonado.
- Claude Code fez a conciliação e as correções apontadas na revisão de Bruno, verificadas com `pytest`, TypeScript, build e testes de navegador. A revisão por outra pessoa continua pendente.

## Página inicial pública (25/11/2026)

- `/` apresenta a rede a visitantes e mostra o início a quem entrou. As demais páginas continuam exigindo sessão, e uma sessão inválida continua levando a `/login`.
- A apresentação usa a arte da identidade aprovada; o fundo de ondas neon foi descartado. Claude Code fez a adaptação.

## Issue #9 — recorte exclusivo de dados — 25/11/2026

- Bruno confirmou limitar esta entrega à sua área: catálogo, gêneros, tags e validação de identidades/versões. Não implementar posts (#3), follow (#5), feed (#6), republicação (#18) ou API/interface dentro desta entrega.
- Catálogo manual com as seis faixas fictícias anteriores, sem expansão. Original, remix, ao vivo e remaster são itens distintos; versões não originais exigem descrição. Chave curada única e estável; correções de metadados não mudam a chave, nem autorizam unir gravações por título/artista.
- Entregues carregador e validador independentes da aplicação/banco, com limpeza de metadados em memória, diagnóstico por entrada/campo e rejeição do conjunto inteiro quando inválido. IDs internos serão atribuídos pelo backend; integrações externas exigem confirmação de equivalência.
- Review única, edição e republicação ficam documentadas como requisitos futuros. Daniel integra persistência, vínculo e validações; Cecília integra seleção/apresentação. Troca da música de uma review continua pendente. A issue #9 não é concluída somente com estes dados.
- O PR exclusivo de dados substitui o #28, preservando sua branch com API/seletor como referência. Os PRs #29–#31 permanecem fechados, sem incorporar suas implementações. O trabalho parte da main atual; a alteração anterior de responsabilidades já consta nessa base e foi preservada.
- Validação: 37 testes de dados passaram sem carregar a infraestrutura de API/banco, incluindo bloqueio explícito de imports da aplicação e das bibliotecas de banco. O validador aprovou as seis entradas. Não foram alterados modelos persistidos, rotas, frontend ou o seed de usuários.
