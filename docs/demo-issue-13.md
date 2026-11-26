# Demonstração — issue #13

Decisões aprovadas por Bruno em 25/11/2026. Planejamento e massa de dados não significam integração concluída. A #13 permanece aberta.

## Fonte musical

[Playlist aprovada: teste projeto trilha](https://open.spotify.com/playlist/7w2BizbgnVVFpwIQScTYvB).
Consulta pública de metadados em 25/11/2026 pelo embed do Spotify, sem autenticação pessoal, download de áudio ou reprodução. A playlist substitui Sozinho por Apesar de Você, conforme confirmação de Bruno.

As referências externas estão em `backend/data/referencias_spotify_demo.json`, separadas do contrato estrito do catálogo. `backend/data/musicas_demo.json` segue o carregador da #39; o catálogo fictício anterior permanece como fixture de versões/homônimos. O backend atribui IDs internos e não deve deduplicar apenas por título/artista. Os IDs externos preservam as gravações escolhidas, inclusive quando o título não identifica o álbum. Álbum e detalhes adicionais das edições ainda precisam de curadoria; não foram inventados. Gêneros/tags são curadoria inicial para teste, não análise acústica.

| Música selecionada | Artista | Versão indicada | Referência |
|---|---|---|---|
| Meteoro - Ao Vivo | Luan Santana | ao_vivo | [Spotify](https://open.spotify.com/track/4ra6zuyLXk69bF3dPVpGGO) |
| Os Anjos Cantam | Jorge & Mateus | original | [Spotify](https://open.spotify.com/track/6ccKu0LwJzOhLAxBwP2PTk) |
| Infiel - Ao Vivo | Marília Mendonça | ao_vivo | [Spotify](https://open.spotify.com/track/38MpAndIjGAyVdcC6npX95) |
| Cheia de Marra | Mc Livinho | original | [Spotify](https://open.spotify.com/track/3jfrTzP1xAPQeixEUxtAvS) |
| Kenny G | Matuê | original | [Spotify](https://open.spotify.com/track/3MkdA6vwF0ifRl86yzTlJW) |
| A Morte do Autotune | Matuê | original | [Spotify](https://open.spotify.com/track/1qyiBNYS01TjMkmoeTLJXN) |
| Negro Drama | Racionais MC's | original | [Spotify](https://open.spotify.com/track/3ytXzEJFeVydFfmUhHvti8) |
| Clareou | Xande de Pilares | original | [Spotify](https://open.spotify.com/track/0ONAzA6lvUfGqvmT8QsfD5) |
| Burguesinha | Seu Jorge | original | [Spotify](https://open.spotify.com/track/35Wfw6eyw39YpOp2lRH11c) |
| Mina do Condomínio | Seu Jorge | original | [Spotify](https://open.spotify.com/track/3QA7VF91ehKfoYEDa5wcJb) |
| Apesar De Você | Chico Buarque, MPB4, Quarteto Em Cy | original | [Spotify](https://open.spotify.com/track/2GAFZG9Z7UGS1iMm4Idrnr) |
| Velha Infância - 2004 Digital Remaster | Tribalistas | remaster | [Spotify](https://open.spotify.com/track/1mSxbLW7fKABfeY4lGpg0E) |
| Cheguei | LUDMILLA | original | [Spotify](https://open.spotify.com/track/6cbZb9mVAc5s8HtwklLoI0) |
| Show das Poderosas | Anitta | original | [Spotify](https://open.spotify.com/track/28aUFtkMnJaqNQkLHR0weV) |
| Deixa Acontecer | Grupo Revelação | original | [Spotify](https://open.spotify.com/track/50mawjudhEofTcUIpRmGXr) |
| Tá Vendo Aquela Lua | Exaltasamba | original | [Spotify](https://open.spotify.com/track/6DjKWVAqXUvMaAzO4U4CIo) |
| Anunciação | Alceu Valença | original | [Spotify](https://open.spotify.com/track/661Ns9G25zHdih4qVshBO7) |
| Asa Branca | Luiz Gonzaga | original | [Spotify](https://open.spotify.com/track/0jAbBolC53vVe33ouZ7D4a) |
| Evidências | Chitãozinho & Xororó | original | [Spotify](https://open.spotify.com/track/1X95pCQG939KCbJL6yVQgw) |
| Dias De Luta, Dias De Gloria | Charlie Brown Jr. | original | [Spotify](https://open.spotify.com/track/006pMMCuRo2TFjh8sNGSov) |

## Personagens e cenários

Nomes fornecidos por Bruno; perfis, opiniões e interações são fictícios e não representam ações reais dessas pessoas. Protagonistas: Bruno Nunes, Cecília Candeia e Daniel Dantas.

Bruno Nunes, Cecília Candeia, Daniel Dantas, Fernando Neto, Gustavo Tenório, Ítalo Matheus, Sofia Lima, Nicole Alverga, Sofia Marques, Pedro Luiz, Lucas Todaro, Davi Góes, Matheus Brito, Gabriel Esberard, Eduardo Travassos, Pedro Correia, Henrique Guimarães, Maria Laura, Giorgio Nicolas, Pedro Henrique, Camila Batista, Larissa Góes, Rodrigo Ângelo, Clarice Rodrigues, Ryan Rodrigues.

Usernames: nome completo em minúsculas, sem acentos, separado por `_`. Credencial exclusiva da futura carga de demonstração: `demo-trilha-13-2026`, armazenada somente como hash pelo adaptador. Não usar senhas pessoais.

- Clareou: Bruno cria raiz; Cecília deriva de Bruno; Daniel deriva de Cecília; Fernando Neto deriva de Bruno; Gustavo Tenório inicia outra raiz.
- Ryan Rodrigues começa sem reviews e curtidas, para demonstrar fallback de conta nova.
- Os demais dados usam semente fixa 13: 25 usuários, 50 reviews, 20 follows e 30 curtidas. Os três protagonistas e os demais perfis são fictícios. Uma review ativa por pessoa/gravação; sem ciclos, auto-follow ou likes duplicados. Datas fixas UTC permitem repetir o cenário; “recentes” significa ordem relativa da carga, não data atual.
- Não há ranking de sugestões ou pontos simulados. Validar personalização e fórmula 4/2/1 com #55 e #43. A massa aleatória não é evidência de qualidade do recomendador; os casos controlados de semelhança pertencem à #55.

## Execução e preservação

Da raiz, com dependências do backend instaladas:

```sh
cd backend
uv sync
uv run python scripts/seed.py --validar-demo
uv run pytest tests_dados -q
```

A validação não abre banco e funciona independentemente da API. Para a futura integração:

```sh
DATABASE_URL=sqlite:///./demo/issue13.db uv run python scripts/seed.py
DATABASE_URL=sqlite:///./demo/issue13.db uv run python scripts/seed.py --reset-demo --confirmar-reset --aplicacao-parada
```

O caminho aceito é exclusivamente `backend/demo/issue13.db`. O seed verifica o contrato antes de gravar e atualmente encerra com código 1 explicando a falta do adaptador. O reset reconstrói um temporário, valida e guarda backup antes da troca atômica. Sem adaptador real disponível, encerra com código 1 preservando o banco. Não há exclusão automática nem carga parcial. `make seed` usa esse novo comando e exige o banco de demonstração; `make seed-minimo` mantém o comportamento anterior de três usuários, exclusivamente para compatibilidade, e não satisfaz a #13.

A orquestração `seed_fake(db, adaptador=None)` recebe sessão exclusiva da carga. Quando integrado, `verificar(db, cenario)` somente lê e valida modelos, capacidades e colisões; `gravar(db, cenario, senha)` usa flush, sem commit/rollback. A orquestração controla a transação e registra `issue13-v1` em `demo_seed_cargas`. Não executar em sessão com mudanças pendentes. Uma marca aplicada evita qualquer reposição de conteúdo apagado, curtidas ou follows removidos. Não usar contagens atuais como critério de repopulação. Alterações futuras de massa exigem nova versão e estratégia explícita; não reaplicar a v1.

## Pendências para Daniel e divisão de trabalho

- Daniel: alinhar adaptador aos modelos de músicas/posts (#3), follows (#4), curtidas (#6) e origens/eventos (#10); revisar importação por chave da #39, colisões e migrações necessárias. Nunca importar metadados por chamada externa a cada renderização.
- Bruno: cenários, catálogo, validação, orquestração e contratos de árvores (#41), reputação (#43) e recomendador (#55).
- Adaptador real ainda não implementado: não há modelos de posts/follows/likes nesta base. Não criar modelos paralelos ou SQL baseado em nomes de colunas presumidos para contornar a integração.
- Mecanismo de reset implementado e testado independentemente dos modelos. Validação do reset com a rede real permanece pendente do adaptador de Daniel.
- Bibliotecas/reescutas/correção entram somente conforme módulos integrados. Não há implementação de API, frontend, OAuth ou streaming nesta entrega.

## Roteiro e evidências

1. Preparar instalação limpa e executar validação dos cenários.
2. Após integração, aplicar carga em banco separado e acessar as contas protagonistas.
3. Abrir Clareou, mostrar corrente, ramificação e raiz independente.
4. Conferir reputação pelos eventos reais quando #43/#10 estiverem integradas.
5. Comparar Descobrir do Ryan com conta que possui sinais; mostrar explicações reais e testar interação/descurtida quando #55/#23/#56 estiverem disponíveis.
6. Editar review, descurtir e deixar de seguir; repetir seed e comprovar preservação. Ensaios alteram o estado: usar reset explícito para voltar ao início quando disponível.

Registrar capturas e resultados reais somente após integração. Não declarar telas, pontos ou sugestões entregues com base em fixtures. Antes de encerrar #13: ativar o teste do núcleo, executar make check/make test e suíte de dados, validar instalação limpa, reset e revisão de outra pessoa. Instruções de entrega institucional seguem README e precisam de confirmação do time; não foram verificadas novas instruções nesta sessão.

## Uso de IA

Codex organizou decisões, consultou metadados públicos da playlist e preparou massa, validações, testes e esta documentação. Nenhuma opinião foi atribuída como real aos participantes. Sem áudio baixado ou treinamento supervisionado.

## Validação executada em 25/11/2026

- Ambiente novo em `/tmp`, instalado a partir de `uv.lock` com `uv sync --frozen`: validação dos cenários e **45 testes de dados passaram**.
- `make test`: **38 passaram e 7 permaneceram skipped**, incluindo `test_seed_fake_popula_a_rede`, pois os modelos persistidos necessários não existem nesta base. O skip não foi removido para esconder essa dependência.
- `make check`: passou usando SQLite separado em `/tmp`.
- Testes adicionais cobrem referências Spotify, determinismo, ciclos, duplicatas, preflight sem escrita, colisão, rollback/repetição e preservação de ações via adaptador de teste. Esses testes não comprovam a persistência real nem o reset integrado.
- Pendente: adaptador real, reset funcional, instalação limpa da rede populada, validação de algoritmos integrados e evidências de interface.


## Continuação aprovada: adaptador, reset e primeiro marco

Daniel entrega os modelos e serviços nas próprias issues. A #13 não criará modelos paralelos. Primeiro marco: carga real e validação pelas APIs; árvores/reputação/Descobrir integram progressivamente, sem encerrar a #13 antecipadamente.

### Contrato proposto para o backend

Após inspecionar os modelos entregues, disponibilizar `app.services.demo_seed.criar_adaptador()`, uma fábrica sem argumentos ou efeitos de escrita. O seed resolve essa fábrica automaticamente; sua ausência produz erro de integração antes de criar banco/carga. Esse caminho é uma proposta a Daniel, não uma interface já entregue por ele.

O objeto retornado implementa:

- `preparar_banco(engine)`: aplicar o esquema oficial e migrações em banco temporário vazio; fechar todas as conexões próprias. Não usar metadados ou SQL de modelos presumidos.
- `verificar(db, cenario)`: somente leitura; conferir esquema, capacidades, colisões, referências e importação por chave estável; rejeitar carga inteira se faltar requisito. Persistência de origem é obrigatória para este cenário.
- `gravar(db, cenario, senha)`: gerar hashes com o serviço oficial, importar músicas, resolver IDs, gravar reviews em ordem de origem, follows/likes e eventos conforme regras entregues. Não controlar commit/rollback.
- `validar(db, cenario)`: verificar a carga inicial completa: 25/20/50/20/30, identidades, origens/ciclos, referências, unicidade, hashes e credenciais das contas protagonistas/Ryan. Lançar erro se houver divergência. Nunca preencher pontos ou rankings fictícios para satisfazer a validação.

O orquestrador exige sessão exclusiva sem mudanças pendentes; registra versão junto com os dados. A marca não é apagada para reparar ações de ensaio. O banco inicial também é preparado em temporário antes de sua publicação.

### Reset e restauração

1. Parar backend e quaisquer processos conectados ao banco de demo.
2. Executar o comando de reset acima, com ambas as declarações explícitas. São recusados links simbólicos, hard links e caminhos diferentes, além de WAL/SHM/journal pendentes. Não remover esses arquivos manualmente para forçar o reset; encerrar conexões e concluir checkpoint usando as ferramentas SQLite apropriadas.
3. O comando prepara e valida um novo banco no mesmo diretório. Validação semântica vem do adaptador; integridade SQLite e foreign keys também são conferidas.
4. O banco anterior é copiado pela API SQLite de backup para `issue13-backup-<data UTC>-<sufixo>.db`. Erro no backup impede troca; cópias incompletas são removidas. Backups válidos ficam locais e são ignorados pelo Git por `*.db`.
5. Fechar conexões antes da substituição atômica. Mudança detectada no arquivo original cancela a operação. A parada da aplicação é requisito declarado pelo operador; a detecção de alterações não substitui essa condição.
6. O comando informa caminhos do banco e backup. Não há limpeza automática de backups.

Para restaurar: parar a aplicação, conferir integridade do backup escolhido, manter uma cópia do estado atual se necessário e copiar o backup para um arquivo temporário no mesmo diretório; somente após validar esse temporário, substituir `backend/demo/issue13.db` com `os.replace`. Não restaurar enquanto houver conexões ou arquivos WAL/journal ativos. A restauração recupera as ações do ensaio e a marca de carga daquela cópia.

### Validação integrada ainda pendente

Após modelos e fábrica reais estarem disponíveis: preparar banco limpo; autenticar Bruno, Cecília, Daniel e Ryan pelas APIs; conferir ausência de hashes nas respostas, músicas/reviews, follows, likes e feed conforme contratos reais. Ativar `test_seed_fake_popula_a_rede` quando existirem seus requisitos. Testar reset e preservação de ações pelos serviços reais. Não criar testes com nomes de rotas ou campos supostos.

Depois: árvore via API; reputação segundo fórmula aprovada; fallback/personalização do Descobrir; evidências visuais quando houver telas integradas. O primeiro marco não encerra a #13.

### Resultado desta continuação

- 56 testes de dados passaram no ambiente isolado instalado a partir do lockfile.
- `make test`: 38 passed, 7 skipped; `make check` com banco separado e `make seed-validar` passaram.
- Testes do reset usam SQLite real em diretórios descartáveis: backup/restauração lógica, falha de preparação/backup/replace, confirmações, caminhos, symlink, WAL, alteração durante preparação e foreign keys inválidas. Testes da fábrica e validação semântica usam adaptador de teste explicitamente identificado.
- Nenhum reset foi executado no banco dos ensaios. Adaptador de produção e testes HTTP com reviews/follows/likes ainda não podem ser implementados sem os modelos e serviços do Daniel.


## Revisão das capas e conciliação da base — 25/11/2026

A base do #32 foi incorporada preservando os registros de demonstração e os registros recentes da main. O catálogo aceita `capa_url` opcional; os cenários de 20 músicas sem esse campo continuam válidos e recebem `None` no carregador.

Uma revisão combinada com o #60 revelou erro de integração: `None` era atribuído à coluna `musicas.capa_url` não anulável na reimportação, impedindo uma segunda inicialização com o mesmo banco. A correção foi implementada no #60: importar cópia do registro com ausência/null convertido para texto vazio, preservando IDs, e alinhar modelo/schema a 2048 caracteres. Testes de regressão cobrem reinício, reimportação, URL longa e remoção de capa. Relato completo: [documentação da correção no PR #60](https://github.com/brunonunesf/miniprojeto3-musica/blob/feat/posts/docs/revisao-integracao-capas.md).

Esta branch não incorpora antecipadamente modelos ou serviços do #60. A correção registrada lá deverá ser mantida quando o adaptador real for integrado. A #13 continua aberta. Não foram enviados avisos/comentários/menções ao time nesta correção; o relato está nos arquivos e descrições técnicas dos PRs.

Validação após atualizar a base: **69 testes de dados passaram**, `make test` teve **48 passed e 7 skipped**, `make check` com banco separado e `make seed-validar` passaram. Esses resultados pertencem à branch de dados; os testes de backend da correção do #60 estão documentados separadamente lá.

## Revisão integral antes do merge — 25/11/2026

Os PRs #32 e #60 foram integrados à main antes desta revisão final. A branch do #59 foi atualizada com essa base, preservando a documentação de feed/descoberta e as decisões existentes. A revisão inclui a estrutura de árvores da #41, que já havia sido incorporada pelo PR #64 nesta branch.

Foram corrigidos dois pontos adicionais e reforçada uma validação:

- `with sqlite3.connect(...)` controla commit/rollback, mas não garante `close()`. As conexões de origem, destino e conferência de integridade do backup agora usam fechamento explícito com `contextlib.closing`, antes de qualquer substituição. Um teste rastreia e confirma o fechamento das três conexões.
- O backend do #60 exige nota inteira de 0 a 10. As 50 reviews preparadas agora incluem nota determinística nessa escala; validação rejeita nota ausente, booleana, decimal, textual ou fora do intervalo. Um teste confronta nota/texto com o schema real `PostCreate`, sem fingir persistência ou origem já implementadas.
- Validação rejeita registros duplicados nas listas de usuários, músicas e reviews, mesmo quando a quantidade de identificadores únicos parecia correta.

O adaptador completo continua pendente: a main agora tem músicas/posts, mas ainda não oferece a fábrica proposta para seed nem todos os requisitos de origens/follows/likes desta carga. O comando continua interrompendo antes de gravar quando a fábrica está ausente. Aprovar e integrar este PR é aceitar a entrega parcial documentada, sem fechar a #13 ou declarar a demonstração completa.

Resultado final sobre a combinação pronta para main: **235 passed e 6 skipped** no `make test` (incluindo dados/árvores); **158 testes de dados** na execução isolada. `make check`, `make seed-validar` e `git diff --check` passaram. TypeScript passou em cópia limpa do frontend: a primeira execução local encontrou somente tipos gerados em `.next` de outras branches; a conferência limpa não reutilizou esse cache e não exigiu alteração no código do front. Não foram executados testes de navegador nesta revisão de dados/backend.
