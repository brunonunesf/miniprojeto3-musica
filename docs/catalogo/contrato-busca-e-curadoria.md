# Busca musical, identidade e curadoria

Decisões aprovadas por Bruno em 26/11/2026. Continuação da entrega de dados #39 na #92;
backend em #3/#21, interface com Cecília na #93. Histórico e sugestões de reescuta são
outro fluxo: esta entrega não conecta contas pessoais nem publica reescutas.

## Fluxo e persistência

1. Usuário autenticado consulta `GET /musicas/busca?q=...`.
2. Catálogo local vem primeiro (até 20 entradas); Spotify e Deezer são consultados
   em paralelo (até 10 resultados por provedor), intercalados na ordem retornada.
   Para mais opções, refine o termo. Consulta vazia mostra somente o catálogo local.
3. Resultado contém `chave`, `musica_id` opcional, `musica` com dados de apresentação,
   `fontes`, links de referência e `selecao_externa` temporária quando há fonte externa.
   `total_local` informa a contagem local; não representa o total nas plataformas.
4. Selecionar ou abandonar o formulário não grava música, referência ou fila.
5. `POST /posts` recebe `musica_id` **ou** `selecao_externa`, além da nota/texto/origem.
   Não envie ambos. Referência externa resolve identidade, cadastra vínculos e publica
   a review na mesma transação. Falha desfaz tudo; o banco arbitra concorrência.
6. O retorno de review mantém `MusicaOut` e o ID interno. Feed, perfil e populares
   não consultam provedores para renderizar cartões.

Seleções são assinadas, vinculadas ao usuário e válidas por 15 minutos. Não são
criptografadas nem contêm credenciais; o cliente não pode alterar metadados. Após
expiração, deve buscar e selecionar novamente. Aprovações/fusões posteriores são
respeitadas quando a identidade é resolvida no momento da publicação.

A resposta expõe estado por fonte: `disponivel`, `aguardando_busca`,
`nao_habilitado`, `sem_acesso`, `limite`, `indisponivel` ou `sem_assinatura`.
Falhas de fonte não eliminam as demais. Sem fontes externas, catálogo local segue
utilizável. Não há resposta simulada de sucesso em produção.

## Contrato de dados e correspondência

`FaixaExterna` é o contrato validado dos adaptadores e dos vínculos de curadoria:

| Campo | Regra |
| --- | --- |
| `servico`, `id_externo`, `url` | Spotify ou Deezer, ID alfanumérico estável e referência HTTP(S) do serviço |
| `titulo`, `artistas` | Obrigatórios; artistas como lista, preservada no snapshot |
| `album`, `duracao_ms`, `isrc` | Opcionais; ausência não autoriza inventar valores |
| `tipo_versao` | original, remix, ao_vivo, remaster ou desconhecida |
| `descricao_versao` | Evidência da edição/apresentação; ausência bloqueia matching novo automático |
| `capa_url` | Opcional; não participa da identidade |

Metadados completos ficam em `referencias_externas.metadados`; o modelo local
mantém os campos compatíveis e recebe chave `externa-<uuid>` ou `curadoria-<uuid>`.
ISRC é normalizado para 12 caracteres maiúsculos, sem hífens. É indexado, **não
único**: um código isolado não prova equivalência.

- Vínculo `(servico, id_externo)` já conhecido reaproveita seu ID interno.
- Vínculo novo entre serviços exige ISRC igual, artistas iguais após normalização,
  diferença de duração de até 2 segundos, título normalizado igual e tipo/descrição
  de versão explícitos e iguais. O título adicionalmente igual é uma restrição
  conservadora: falsos negativos seguem para curadoria.
- Normalização remove acentos, ignora caixa e reduz espaços; não elimina palavras
  de versão nem tenta equivalência aproximada entre nomes de artistas.
- Ausência de rótulo não significa original. Sem evidência, usar `desconhecida`.
- Identidades já persistidas diferentes nunca são fundidas pela busca/publicação.
  Mesmos títulos/artistas ou ISRCs conflitantes geram fila somente após publicação.
- Duas reviews próprias em identidades a fundir impedem a fusão. Bruno resolve o
  conflito com os autores pelo fluxo normal; o comando nunca apaga reviews.

A curadoria pode aprovar um vínculo mesmo quando faltam os critérios automáticos,
registrando autor, motivo e dados na auditoria. Separar um par na fila marca que
são gravações distintas. Fundir transfere vínculos, reviews, lugares de reviews
apagadas e pedidos aprovados; preserva IDs de reviews e mantém a música anterior
como alias do destino. A consulta por ID antigo resolve o destino. Chaves curadas
antigas continuam reservadas, sem ressuscitar a identidade na reimportação.

## Inclusão e classificação

- `POST /musicas/solicitacoes`: título e artista obrigatórios, versão opcional,
  referência HTTP(S) ou justificativa obrigatória. Não busca nem baixa a URL enviada.
- `GET /musicas/solicitacoes?offset=0&limit=20`: somente pedidos do usuário da sessão,
  mais recentes primeiro. Não existe endpoint público administrativo de aprovação.
- Reenvio do mesmo título/artista/versão pendente pelo mesmo usuário reutiliza o
  pedido; a lista informa pendente, aprovado ou recusado, motivo e música aprovada.
- Aprovar pode cadastrar uma música curada ou apontar para uma já existente.
  O usuário volta ao formulário pelo link para publicar; nenhum rascunho é salvo.
- Músicas importadas podem receber reviews sem gêneros/tags. Bruno classifica depois;
  a descoberta existente sem sinais continua operando. A curadoria protege os campos
  locais contra sobrescrita pela importação de startup.

## Operação administrativa

Execute de `backend/`, usando `DATABASE_URL` do banco desejado. Faça backup de um
banco existente antes de migrar. A migração é aditiva/idempotente, preserva IDs e
não importa catálogo. A subida da API também aplica a atualização de esquema existente.

```sh
uv run python scripts/curadoria_catalogo.py migrar
uv run python scripts/curadoria_catalogo.py migrar --aplicar
uv run python scripts/curadoria_catalogo.py listar
uv run python scripts/curadoria_catalogo.py executar --arquivo lote.json --autor Bruno
uv run python scripts/curadoria_catalogo.py executar --arquivo lote.json --autor Bruno --aplicar
```

Sem `--aplicar`, todas as operações são executadas e revertidas em transação; IDs
propostos são provisórios. Um erro reverte o lote completo, inclusive auditoria.
`listar` retorna pedidos, músicas pendentes, referências, correspondências e auditoria.
O arquivo é um array de operações. Campos desconhecidos/limites inválidos são rejeitados.
Exemplo de aprovação e classificação (IDs devem ser substituídos pelos da prévia):

```json
[
  {
    "acao": "aprovar", "pedido_id": 12, "motivo": "Referência conferida",
    "dados": {
      "titulo": "Faixa independente", "artista": "Artista",
      "tipo_versao": "desconhecida", "generos": [], "tags": []
    }
  },
  {
    "acao": "classificar", "musica_id": 37, "motivo": "Curadoria de gênero",
    "dados": {
      "titulo": "Faixa", "artista": "Artista", "tipo_versao": "original",
      "descricao_versao": "Edição confirmada", "generos": ["mpb"], "tags": ["acustico"]
    }
  }
]
```

Outras operações:

- Aprovar música existente: `acao=aprovar`, `pedido_id`, `musica_id`, `motivo`.
- Recusar: `acao=recusar`, `pedido_id`, `motivo`.
- Vincular plataforma: `acao=vincular`, `musica_id`, `referencia` com `FaixaExterna`, `motivo`.
- Confirmar músicas distintas: `acao=separar`, `musica_id`, `outra_musica_id`, `motivo`.
- Fundir: `acao=fundir`, `musica_id` destino, `outra_musica_id` origem e `motivo`.
  **Pare a API antes de aplicar** e use também `--aplicacao-parada`; reinicie depois
  para reconstruir as árvores em memória. A prévia mostra quantas reviews serão
  transferidas; colisões de autoria bloqueiam a operação.

## Provedores e evidências

Por padrão ambos ficam desabilitados. Configure no servidor, nunca em variáveis
`NEXT_PUBLIC_*`:

```dotenv
MUSICA_SELECTION_SECRET=trocar-por-segredo-aleatorio-de-no-minimo-32-bytes
SPOTIFY_BUSCA_VALIDADA=false
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
DEEZER_BUSCA_VALIDADA=false
```

Use a mesma chave de seleção em todos os workers. Trocar a chave invalida seleções
em aberto. Para habilitar um provedor, Daniel deve registrar data, aplicativo/conta,
condições de acesso e resultado de uma busca real, sem expor credenciais, então
alterar a respectiva flag para `true`. Os logs registram fonte e estado de falha,
sem tokens, termos pesquisados ou histórico pessoal.

Spotify usa client credentials, `GET /v1/search?type=track&market=BR&limit=10` e
metadados opcionais. Token fica apenas em memória do servidor até expirar;
401 invalida o token para a próxima busca. Deezer usa `/search/track` e detalhe
`/track/{id}` para ISRC/contributors, com até dez detalhes por busca. Há prazo
global de seis segundos por fonte e timeout de quatro segundos por chamada.

Referências oficiais consultadas:

- [Spotify: busca](https://developer.spotify.com/documentation/web-api/reference/search).
- [Spotify: client credentials](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow).
- [Spotify: mudanças de fevereiro de 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).
- [Deezer: busca](https://developers.deezer.com/api/search): retornou login/aceite de
  termos na consulta desta entrega. O adaptador tem testes simulados; contrato e
  disponibilidade real ainda precisam de validação autenticada pelo responsável.

Nenhum teste simulado comprova acesso oficial real. Não houve habilitação de
provedores, deploy ou alteração do banco de desenvolvimento nesta entrega.

## Verificação local

```sh
# Da raiz do repositório:
uv run --directory backend pytest -q
npm ci --prefix frontend
npm run build --prefix frontend
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e --prefix frontend -- tests/catalogo-externo.spec.ts tests/reviews.spec.ts tests/catalogo-identidade.spec.ts
```

O último comando usa o Chrome instalado. Para Chromium gerenciado pelo Playwright,
instale-o com `npx playwright install chromium` em `frontend/` e omita a variável
`PLAYWRIGHT_CHANNEL`. Os testes usam bancos descartáveis; nenhum exige habilitar
os provedores. O teste de publicação externa simula apenas a resposta de busca:
a assinatura da seleção, a publicação e a consulta do catálogo usam a API real.
