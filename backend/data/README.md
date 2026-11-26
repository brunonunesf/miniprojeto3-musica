# Catálogo musical — dados da issue #9

Este catálogo contém **seis faixas e artistas fictícios de demonstração**. Não representa músicas reais nem comprova equivalência com gravações de serviços externos. Esta entrega é de dados: não popula banco, não cria API e não integra formulários ou reviews.

## Validar sem iniciar a aplicação

Na raiz do repositório, com as dependências do backend já instaladas:

```bash
backend/.venv/bin/python backend/scripts/validar_catalogo.py
backend/.venv/bin/python backend/scripts/validar_catalogo.py /caminho/para/outro-catalogo.json
backend/.venv/bin/python -m pytest backend/tests_dados -q
```

Também é possível executar de `backend/` com `uv run python scripts/validar_catalogo.py` e `uv run pytest tests_dados -q`. O catálogo padrão é resolvido pelo local do módulo, independentemente da pasta atual. A ferramenta devolve código 0 no sucesso e 1 em erro de leitura ou validação, indicando entrada (contagem a partir de 1) e campo quando aplicável. Ela não altera o JSON nem grava dados.

Os testes ficam em `tests_dados/`, separados de `tests/`, cujo `conftest.py` prepara a infraestrutura de API/banco. Execute o comando específico acima; o `make test` atual continua cobrindo a suíte existente do time.

## Contrato dos registros

O arquivo é um array JSON UTF-8 não vazio. Os campos abaixo são obrigatórios, exceto `capa_url`; campos extras continuam recusados.

| Campo | Regra |
|---|---|
| `chave_catalogo` | Única no arquivo, estável, 1–100 caracteres, somente `a-z`, `0-9`, `_` e `-`. Não é normalizada. |
| `titulo`, `artista` | 1–200 caracteres após limpar espaços excedentes. Preservam caixa e acentos. |
| `tipo_versao` | `original`, `remix`, `ao_vivo` ou `remaster`. |
| `descricao_versao` | Até 200 caracteres após limpar espaços; não pode ficar vazia para remix, ao vivo ou remaster. Na original pode ser vazia. |
| `capa_url` | Opcional, omitida ou `null` quando não houver capa. Quando preenchida, URL absoluta HTTP/HTTPS de até 2048 caracteres; não aceita texto vazio, caminho local ou esquemas como `data:` e `javascript:`. |
| `generos`, `tags` | Listas não vazias de textos; cada termo tem 1–80 caracteres após limpeza. Espaços são normalizados, aplica-se `casefold` e repetições são removidas, preservando a primeira ordem. |

A normalização produz novos registros em memória. O arquivo de origem e suas chaves não são reescritos. Não há remoção automática de acentos, classificação por IA ou vocabulário fechado: mantenha os termos consistentes com o catálogo existente e revise novos sinônimos manualmente.

## Curadoria de identidades e versões

1. Antes de adicionar uma faixa, confirme manualmente se a gravação/edição já está no catálogo. Se existir, reutilize sua chave nas referências; não duplique o registro.
2. Outra gravação ou edição recebe uma chave nova e permanente. Original, remix, ao vivo e remaster são itens distintos; descreva a versão específica, por exemplo nome do remix, apresentação ou edição/ano. Duas apresentações ao vivo diferentes também precisam de chaves e descrições diferentes.
3. Título/artista não são identificadores. O mesmo título com outro artista é permitido; metadados iguais não autorizam fundir gravações. A ferramenta valida a estrutura e a unicidade das chaves, mas não decide equivalência musical.
4. Para corrigir grafia, descrição, gênero ou tags da mesma entrada, mantenha a chave. Não reutilize uma chave antiga para outra gravação e não renomeie chaves para acompanhar mudanças de título.
5. Valide o conjunto inteiro antes de entregar. Se qualquer entrada falhar, o carregador lança erro e não retorna uma lista parcial.

Os exemplos cobrem uma original com remix, ao vivo e remaster, outro artista com o mesmo título e uma faixa adicional. O cadastro de músicas reais, expansão do catálogo e matching externo ficam para outra entrega combinada.

## Reutilização pelo backend (integração futura)

A partir de `backend/`:

```python
from catalogo_musical import carregar_catalogo

registros = carregar_catalogo()  # list[dict], todos validados e normalizados
# Ou carregar_catalogo(caminho) para um catálogo específico.
```

`validar_catalogo(conteudo)` também aceita o array já lido. Falhas levantam `ErroCatalogo` (subclasse de `ValueError`). As funções não importam `app`, não abrem banco e não fazem chamadas externas.

A `chave_catalogo` identifica a entrada curada; o **ID interno do banco será atribuído e preservado pelo backend**, que deve integrar a importação sem duplicar identidades. Os registros desta entrega não incluem `id` de banco. Spotify/Deezer só poderão ser associados ao mesmo item após confirmar a gravação; título/artista ou serviço diferente não bastam. Esta entrega não adiciona IDs externos, autenticação com provedores ou matching.

## Limites e trabalho restante

- **Bruno (dados):** catálogo, gêneros, tags e consistência das identidades/versões, entregues aqui.
- **Daniel (backend):** persistência/importação, consultas, vínculo review/música e validações, incluindo uma review ativa por pessoa/item musical e proteção contra envios simultâneos.
- **Cecília (frontend):** seleção e apresentação musical nas reviews, tratamento de referência inválida e opções ao tentar criar outra review da mesma versão.

Requisitos futuros confirmados neste chat: uma review ativa por pessoa/versão; editar texto preserva a identidade musical; republicar reutiliza a review, com comentário opcional e intervalo de 24h; edição real volta a destacar o mesmo cartão, sem criar avisos por edição e sem consumir esse intervalo. Esses comportamentos **não estão implementados nesta entrega** e dependem das issues e áreas correspondentes. Trocar a música de uma review continua pendente.

A issue #9 permanece aberta para integração e validação conjunta. As branches dos PRs #28–#31 preservam referências anteriores, sem autorização implícita para integrar código de outras áreas. O PR de dados substitui o #28; #29–#31 continuam fechados.

## Capas — ajuste da revisão do PR #32

Os seis exemplos fictícios usam `capa_url: null`; não foram associadas capas de artistas reais a faixas fictícias. Catálogos anteriores sem o campo continuam válidos. O retorno do carregador inclui `capa_url` como texto ou `None`, e pode ser serializado diretamente em JSON. URLs passam pela normalização padrão de `HttpUrl` (por exemplo, barra final no domínio); parâmetros e caminho são preservados. O limite de 2048 caracteres é aplicado ao valor normalizado.

A validação é estrutural e não testa existência, disponibilidade, formato do arquivo ou permissão de uso da imagem; não realiza acesso à rede. O front pode usar uma capa padrão quando o valor estiver ausente ou a imagem falhar. Persistência e inclusão nas respostas da API ficam com o backend; a URL não participa da identidade nem da deduplicação musical.

## Catálogo selecionado por ambiente

`carregar_catalogo()` e o startup do backend usam `CATALOGO_MUSICAL_PATH` quando definida. Caminho relativo é resolvido a partir de `backend/`, independentemente do diretório de execução. Exemplo: `CATALOGO_MUSICAL_PATH=data/musicas_demo.json`. Um argumento explícito a `carregar_catalogo(caminho)` tem precedência; sem variável, o padrão continua `data/musicas.json` (seis fictícias). Configuração vazia/inválida falha, sem retornar silenciosamente ao padrão.

O validador de linha de comando também usa a configuração quando não recebe arquivo explícito. Essa seleção não baixa músicas nem altera IDs. Na demonstração, iniciar seed e aplicação com a mesma variável para não importar outro catálogo ao reiniciar.
