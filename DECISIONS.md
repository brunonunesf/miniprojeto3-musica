# Decisões do time

**Time:** Bruno Nunes (@brunonunesf), Cecília Candeia (@cec1l14) e Daniel Dantas (@dnieldantas).

Documento inicial baseado nas mensagens de texto da conversa de WhatsApp. Ideias discutidas não significam funcionalidades prontas nem escopo fechado.

## Produto

- **Público inicial proposto:** ouvintes que descobrem músicas pelas indicações de amigos e outros ouvintes, com atenção à divulgação de artistas pequenos e independentes. O recorte mais específico ainda será validado pelo time.
- **Problema:** recomendações isoladas não mostram a corrente de descobertas nem reconhecem as pessoas que ajudaram uma música a chegar a novos ouvintes.
- **Como a rede resolve:** conectar reviews derivadas às suas origens e tornar visível a contribuição das pessoas por meio de árvores de recomendações e reputação.
- **Impacto pretendido:** incentivar a descoberta e a divulgação de artistas com menor visibilidade, como Daniel destacou na conversa.
- **Sinal de sucesso proposto, a validar:** pessoas descobrem uma música por outra pessoa e publicam uma review ligada à recomendação original.

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

| Funcionalidade | Situação | Dono |
|---|---|---|
| Autenticação, posts, feed, perfil, follow, curtidas e comentários | Núcleo a implementar conforme os testes da base | A combinar |
| Seed de exemplo no nicho musical | Adaptar ao produto | A combinar |
| Reviews e árvores de recomendações | Diferencial proposto | A combinar |
| Reputação distribuída | Proposta; fórmula em aberto | A combinar |
| Bibliotecas de descobertas e recomendações | Ideia descrita por Daniel | A combinar |
| Grupos de amigos e conversa sobre a semana musical | Sugestão a avaliar | A combinar |
| Mensagens diretas | Sugestão a avaliar | A combinar |

## Escolhas técnicas pendentes

A stack inicial é a do esqueleto oficial: FastAPI + SQLAlchemy + SQLite e Next.js + TypeScript + Tailwind. A árvore de recomendações sugere explorar uma estrutura de árvores, mas nenhuma representação, algoritmo ou complexidade foi escolhida ou medida ainda.

Também faltam definir catálogo e identificação das músicas, eventual integração externa, regras para vincular reviews à origem e exibição das árvores. Não há integração com streaming aprovada.

A conversa menciona aplicação de ML, mas a proposta específica não está descrita nos textos disponíveis. Não se assume que reputação seja ML; a aplicação e sua exigência precisam ser confirmadas pelo time no material do curso.

## Organização e entrega

- O time decidirá a divisão das features e revisará as contribuições entre si.
- Não foram criadas issues ou PRs nesta preparação, conforme pedido de Bruno.
- O guia oficial menciona GitHub Classroom. O convite não foi fornecido; confirmar o destino exigido para a entrega antes da submissão.

## Uso de IA

Codex foi usado para ler os textos exportados do WhatsApp, separar as ideias sobre música, consultar o material do miniprojeto e preparar o repositório e esta documentação. Não implementou funcionalidades da rede social, não transcreveu áudios e não definiu decisões de produto ausentes da conversa.
