# Funcionalidades opcionais: esboço e parecer de experiência (#53)

26/11/2026. Texto redigido com Claude Code a pedido de Cecília. É uma **proposta**: a priorização é do trio, e nada aqui está implementado. Uma eventual implementação exige issues próprias. Os esforços são estimativas relativas (pequeno, médio, grande), sem medição.

## Resumo

| Funcionalidade | Parecer para 27/11 | Depois da entrega | Esforço estimado |
|---|---|---|---|
| Grupos de amigos e semana musical | Não implementar | Primeira opção a avaliar | Médio a grande |
| Mensagens diretas | Não implementar | Depois dos grupos, se houver demanda | Grande |
| Spotify: confirmar reescutas | Não integrar | Só como teste restrito, se houver conta Premium | Médio, com limite de acesso |
| Deezer: confirmar reescutas | Não integrar | Reavaliar quando houver acesso oficial confirmado | Não estimado |

O diferencial da rede é a corrente de descobertas (review derivada, árvore e reputação). Nenhum dos itens acima é necessário para demonstrá-la.

## Grupos de amigos e semana musical

**Caso de uso.** Um grupo pequeno de pessoas que já se conhecem quer ver, num só lugar, o que cada uma avaliou na semana e comentar.

**O que já existe e o que faltaria**

| Já existe | Atende | Não atende |
|---|---|---|
| Seguir e feed | Acompanhar pessoas escolhidas | O feed mistura todo mundo que se segue e não é compartilhado entre o grupo |
| Comentários | Conversar sobre uma review | Não há conversa do grupo |
| Compartilhar link da review | Levar uma review a outro aplicativo | A conversa acontece fora da rede |

**Significado de semana musical.** São as reviews publicadas pelos membros de segunda a domingo. Não representa o que a pessoa ouviu: a rede não tem histórico de escuta e a tela não deve sugerir que tem.

**Fluxos propostos**

- Criar: nome do grupo; quem cria é a primeira pessoa membro e administradora.
- Entrar: por link de convite gerado pela administração. Sem busca pública de grupos na primeira versão.
- Sair: a qualquer momento. Se a administradora sair, a função passa para o membro mais antigo; sem membros, o grupo deixa de existir. As reviews não são apagadas.
- Publicações: não há publicação própria do grupo. A tela reúne as reviews que os membros já publicam.

**Esboço**

```text
+--------------------------------------------------+
| Sexta do Vinil                     [Convidar]    |
| 5 membros                          [Sair]        |
+--------------------------------------------------+
| Semana musical: 23 a 29/11        [<]  [>]       |
| 8 reviews publicadas pelos membros               |
+--------------------------------------------------+
| (cartão de review, o mesmo do feed)              |
| (cartão de review, o mesmo do feed)              |
+--------------------------------------------------+
| Estado vazio: "Ninguém do grupo publicou         |
| nesta semana."                                   |
+--------------------------------------------------+
```

**Proposta mínima.** Criar, entrar por convite, sair, listar membros e mostrar a semana com os cartões existentes. Sem conversa própria, ranking ou comparação de gosto.

**Esforço (estimativa): médio a grande.** Back: grupos, membros, convites, permissões e consulta por período. Front: três telas, reaproveitando os cartões.

## Mensagens diretas

**Caso de uso.** Indicar uma música a uma pessoa específica, em particular, e conversar sobre ela.

**Comparação.** Comentários são visíveis a quem acessa a review; compartilhar leva o link a outro aplicativo, que já resolve a conversa privada sem custo para a rede; seguir e feed não permitem dirigir uma indicação a alguém.

**Quem contata quem.** Só pessoas que se seguem mutuamente podem iniciar conversa. Deixar de seguir impede novas mensagens e mantém o histórico visível para as duas. Não há grupo, pedido de mensagem nem contato de desconhecidos.

**Compartilhar review.** A mensagem pode anexar uma review, exibida como cartão. Se ela for apagada, o cartão mostra "review apagada", sem o conteúdo. Receber uma mensagem não cria vínculo de origem nem pontua: isso continua exigindo uma review derivada.

**Esboço**

```text
Caixa de conversas              Conversa com Júlia
+---------------------------+   +---------------------------+
| (J) Júlia            2    |   | Júlia                     |
|     "escuta essa"         |   |  [cartão: Maré · 9/10]    |
| (P) Pedro                 |   |  escuta essa              |
|     você: valeu!          |   |             já vou ouvir  |
| Vazio: "Nenhuma conversa. |   | [escreva...]  [Enviar]    |
| Siga alguém que siga      |   | Falha: o texto continua   |
| você para começar."       |   | no campo.                 |
+---------------------------+   +---------------------------+
```

**Proposta mínima.** Conversas 1-para-1, texto, anexo de review, histórico paginado e indicação de não lidas, sem tempo real (atualização ao abrir).

**Esforço (estimativa): grande.** Além das telas e do armazenamento, mensagens privadas pedem controle de acesso testado, denúncia ou bloqueio e regras de exclusão, que a rede ainda não tem.

## Spotify e Deezer

Nenhuma integração foi implementada e nenhum botão de conectar foi criado. Nada foi testado com conta ou chave real. A consulta abaixo foi feita em 26/11/2026.

### Spotify

Segundo a documentação oficial:

- A rota de músicas tocadas recentemente consta como disponível e exige a permissão `user-read-recently-played` ([referência](https://developer.spotify.com/documentation/web-api/reference/get-recently-played), [mudanças de fevereiro de 2026](https://developer.spotify.com/documentation/web-api/references/changes/february-2026)).
- Em modo de desenvolvimento, o dono do aplicativo precisa de Spotify Premium e até 5 usuários podem usar a integração ([modos de cota](https://developer.spotify.com/documentation/web-api/concepts/quota-modes), [comunicado de 06/02/2026](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security)).
- O modo estendido só aceita organizações, com requisitos como pelo menos 250 mil usuários ativos por mês ([modos de cota](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)).

**Parecer.** O acesso para o público da rede está bloqueado para o time. Um teste com até 5 pessoas parece possível em tese, mas depende de conta Premium e não foi verificado na prática. Não declarar integração entregue.

### Deezer

As páginas oficiais consultadas ([início](https://developers.deezer.com/), [API](https://developers.deezer.com/api)) pedem login e não informam se há criação de novos aplicativos. Relatos de terceiros na [comunidade da Deezer](https://en.deezercommunity.com/other-devices-49/create-developer-app-82800) indicam que o cadastro está fechado, o que não foi confirmado em fonte oficial.

**Parecer.** Viabilidade **não comprovada**. Não criar telas de conexão.

### Experiência, caso um acesso venha a existir

1. No perfil, "Conectar", com explicação do que será lido. Opção de desconectar sempre visível.
2. Lista "Você ouviu de novo?" apenas com músicas que a pessoa já avaliou.
3. Nada é publicado sozinho: a pessoa confirma, com comentário opcional, respeitando um aviso por música a cada 24 horas.
4. Estados: permissão negada, conexão expirada, lista vazia, erro e serviço indisponível.

**Alternativa manual.** Hoje a pessoa publica ou edita a própria review. O aviso "Ouvi novamente" pertence à #45 e ainda não existe.
