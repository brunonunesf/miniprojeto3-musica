# Aceite do catálogo e identidade musical — #39

Validação em 26/11/2026, baseada na main `0be5578`. Entrega exclusiva de dados, documentação e evidências; sem mudança de API, banco ou interface de produto.

## Resultados

| Critério | Evidência e resultado |
|---|---|
| Campos mínimos, normalização e deduplicação | Carregador e testes de catálogo: chaves únicas/estáveis, rejeição de inválidos, gêneros/tags normalizados sem fundir por metadados. |
| Catálogo consumível por API e seed | Validadores aprovam as seis fictícias e as 20 reais; testes de dados cobrem demo/seed e referências Spotify. |
| Duas reviews da mesma gravação | Teste de API e teste de navegador com duas contas: respostas de criação contêm o mesmo `musica.id`. |
| Versões e homônimos separados | API e navegador: cinco identidades de Horizonte (original, remix, ao vivo, remaster e outro artista), todas publicáveis pela mesma conta. |
| IDs preservados na reimportação | Testes de API verificam importação idempotente e segunda inicialização. |
| Regra entre serviços e entrada manual | Contrato atualizado no README de dados; nenhuma equivalência externa presumida ou implementada. |

Comando `backend/.venv/bin/python -m pytest backend/tests_dados backend/tests/test_musicas.py backend/tests/test_posts.py -q`: **217 passed**, com um aviso de depreciação de Starlette/httpx. Build e typecheck do frontend aprovados.

Os gêneros e tags foram inspecionados como listas abertas; não houve necessidade de alterar os dados. As chaves, o catálogo, as referências Spotify e os IDs permanecem preservados.

## Reprodução pela interface real

O teste `frontend/tests/catalogo-identidade.spec.ts` usa Chrome, formulários reais e respostas da API, sem interceptadores/mocks. Cada execução do Playwright inicia backend/frontend e cria um banco SQLite temporário; não usa banco pessoal. São duas contas isoladas, com cadastro e publicação pela tela.

Na raiz, instalar dependências conforme o setup do projeto. Em `frontend/`:

```bash
npm run build
PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/catalogo-identidade.spec.ts --project=desktop --output=test-results/issue39-tecnico
CATALOGO_MUSICAL_PATH=data/musicas_demo.json PLAYWRIGHT_CHANNEL=chrome npx playwright test tests/catalogo-identidade.spec.ts --project=desktop --output=test-results/issue39-real
```

Deixar portas 3000 e 8000 livres. O segundo comando usa as seis fictícias; o terceiro usa as 20 reais. Cada execução aprovou **1 teste**. Chrome local é requisito para `PLAYWRIGHT_CHANNEL=chrome`; o projeto também suporta navegador instalado pelo Playwright.

O roteiro automatizado equivale a: cadastrar Ana, selecionar/publicar música, cadastrar Bia em sessão separada, selecionar/publicar a mesma gravação e comparar o ID retornado. No catálogo técnico, Ana também publica as demais versões e o homônimo. Bia consulta o perfil de Ana, passa a segui-la e vê suas reviews no feed. As capturas abaixo registram detalhe, perfil e feed; não são mockups.

| Tela | Técnico | Real |
|---|---|---|
| Detalhe | [Captura](tecnico-detalhe.png) | [Captura](real-detalhe.png) |
| Perfil | [Captura](tecnico-perfil.png) | [Captura](real-perfil.png) |
| Feed | [Captura](tecnico-feed.png) | [Captura](real-feed.png) |

## Limites

A checagem visual foi executada por automação de navegador em desktop; não é revisão manual humana nem teste de disponibilidade/licença de capas externas. Não se confirma equivalência Spotify/Deezer. Backend/frontend existentes são exercitados apenas nos cenários da #39. O encerramento depende de revisão de outra pessoa e merge do PR; esta evidência não encerra #3 ou #33.
