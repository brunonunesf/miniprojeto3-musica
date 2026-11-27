import { expect, test, type Page } from "@playwright/test";

const pessoa = (id: number, name: string) => ({ id, username: name.toLowerCase(), name, bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" });
const bia = pessoa(901, "Bia");
const caio = pessoa(902, "Caio");
const musica = {
  id: 1, chave_catalogo: "teste-1", titulo: "Maré", artista: "Faroleiros",
  tipo_versao: "original", descricao_versao: "", generos: [], tags: [], capa_url: "",
};
const review = (id: number, autor = bia) => ({ id, texto: "Ótima.", nota: 7, tem_texto: true, musica, autor, created_at: autor.created_at });
const pagina = (items: object[], total = items.length, offset = 0) => ({ json: { items, total, offset, limit: 10 } });

const naApi = (caminho: string) => (url: URL) => url.port === "8000" && url.pathname === caminho;
const semEstouro = (page: Page) => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`origem_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

test("reputação é buscada de novo depois de curtir, sem sumir em falha", async ({ page }) => {
  await entrar(page);
  let reputacao = 4;
  let falhar = false;
  await page.route(naApi("/usuarios/bia"), (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    if (falhar) return route.fulfill({ status: 500, json: {} });
    return route.fulfill({ json: { ...bia, seguidores: 0, seguindo: 0, eu_sigo: false, reputacao } });
  });
  await page.route(naApi("/usuarios/bia/posts"), (route) =>
    route.fulfill(pagina([{ ...review(7), curtidas: 0, curtido_por_mim: false }])),
  );
  await page.route(naApi("/posts/7/curtir"), (route) => {
    const metodo = route.request().method();
    if (metodo === "OPTIONS") return route.fallback();
    const curtiu = metodo === "POST";
    reputacao = curtiu ? 8 : 4;
    return route.fulfill({ json: { curtidas: curtiu ? 1 : 0, curtido_por_mim: curtiu } });
  });

  await page.goto("/usuarios/bia");
  await expect(page.getByText("4 de reputação")).toBeVisible();
  await page.getByRole("button", { name: "Curtir", exact: true }).click();
  await expect(page.getByText("8 de reputação")).toBeVisible();

  falhar = true;
  await page.getByRole("button", { name: "Descurtir" }).click();
  await expect(page.getByText("Não foi possível atualizar a reputação.", { exact: false })).toBeVisible();
  await expect(page.getByText("8 de reputação")).toBeVisible();
});

test("autora corrige a origem com confirmação e sem falso sucesso", async ({ page }) => {
  await entrar(page);
  const eu = await page.evaluate(async () =>
    (await fetch("http://localhost:8000/auth/eu", { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } })).json(),
  );
  const minha = { ...review(7, eu), origem_id: 3, origem: { id: 3, autor: { name: "Bia" } } };
  await page.route(naApi("/openapi.json"), (route) => route.fulfill({ json: { paths: { "/posts/{post_id}/origem": { patch: {} } } } }));
  await page.route(naApi("/posts/7"), (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    return route.fulfill({ json: minha });
  });
  await page.route(naApi("/musicas/1/reviews"), (route) => route.fulfill(pagina([minha, review(3), review(4, caio)])));
  let falhar = true;
  const corpos: unknown[] = [];
  await page.route(naApi("/posts/7/origem"), (route) => {
    if (route.request().method() !== "PATCH") return route.fallback();
    corpos.push(route.request().postDataJSON());
    return falhar
      ? route.fulfill({ status: 422, json: { detail: "a origem escolhida criaria um ciclo" } })
      : route.fulfill({ json: { ...minha, origem_id: 4, origem: { id: 4, autor: { name: "Caio" } } } });
  });

  await page.goto("/posts/7");
  await expect(page.getByText("Hoje: a review de Bia.")).toBeVisible();
  await page.getByRole("button", { name: "Corrigir origem" }).click();
  // Só reviews de outras pessoas que não sejam a origem atual.
  await expect(page.getByRole("radio")).toHaveCount(1);
  await page.getByRole("button", { name: "Continuar" }).click();
  await expect(page.getByText("Escolha a nova origem.")).toBeVisible();
  await page.getByRole("radio", { name: /Review de Caio/ }).check();
  await page.getByRole("button", { name: "Continuar" }).click();
  await expect(page.getByText("serão recalculados", { exact: false })).toBeVisible();
  expect(corpos).toHaveLength(0);
  await page.getByRole("button", { name: "Confirmar correção" }).click();
  await expect(page.getByText("a origem escolhida criaria um ciclo")).toBeVisible();
  await expect(page.getByText("Origem corrigida.")).toHaveCount(0);
  await expect(page.getByText("Hoje: a review de Bia.")).toBeVisible();
  expect(await semEstouro(page)).toBe(true);

  falhar = false;
  await page.getByRole("button", { name: "Continuar" }).click();
  await page.getByRole("button", { name: "Confirmar correção" }).click();
  await expect(page.getByText("Origem corrigida.")).toBeVisible();
  await expect(page.getByText("Hoje: a review de Caio.")).toBeVisible();
  await expect(page.getByText("A partir da review de Caio")).toBeVisible();
  expect(corpos).toEqual([{ origem_id: 4 }, { origem_id: 4 }]);
});

test("sem a rota no servidor, a correção de origem não aparece", async ({ page }) => {
  await entrar(page);
  const eu = await page.evaluate(async () =>
    (await fetch("http://localhost:8000/auth/eu", { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } })).json(),
  );
  await page.route(naApi("/posts/7"), (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    return route.fulfill({ json: { ...review(7, eu), origem_id: 3, origem: null } });
  });
  const esquema = page.waitForResponse((resposta) => resposta.url().endsWith("/openapi.json"));
  await page.goto("/posts/7");
  await esquema;
  await expect(page.getByRole("button", { name: "Editar review" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Corrigir origem" })).toHaveCount(0);
});

test("Descobrir avisa quando o servidor ainda não tem sugestões", async ({ page }) => {
  await entrar(page);
  await page.getByRole("link", { name: "Descobrir", exact: true }).click();
  await expect(page.getByText("ainda estão em preparação", { exact: false })).toBeVisible();
  await expect(page.getByRole("link", { name: "Pesquisar músicas" })).toBeVisible();
});

test("Descobrir mostra motivos, pagina, trata falha e vazio", async ({ page }) => {
  await entrar(page);
  let modo: "falha" | "lista" | "vazio" = "falha";
  const sugestao = (id: number) => ({ review: review(id), explicacao: `Motivo ${id}` });
  await page.route(naApi("/descobrir"), (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    if (modo === "falha") return route.fulfill({ status: 500, json: {} });
    if (modo === "vazio") return route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 10, personalizada: true } });
    const offset = Number(new URL(route.request().url()).searchParams.get("offset"));
    return route.fulfill({ json: { items: [sugestao(offset + 1)], total: 2, offset, limit: 10, personalizada: false } });
  });

  await page.goto("/descobrir");
  await expect(page.getByText("O serviço está indisponível.", { exact: false })).toBeVisible();
  modo = "lista";
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(page.getByText("Motivo 1")).toBeVisible();
  await expect(page.getByText("A personalização começa", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Carregar mais" }).click();
  await expect(page.getByText("Motivo 2")).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Carregar mais" })).toHaveCount(0);
  expect(await semEstouro(page)).toBe(true);

  modo = "vazio";
  await page.getByRole("button", { name: "Atualizar sugestões" }).click();
  await expect(page.getByText("Nenhuma sugestão por enquanto.")).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(0);
});
