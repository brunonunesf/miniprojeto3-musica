import { expect, test, type Page, type Route } from "@playwright/test";

function review(id: number) {
  const autor = { id: 99, username: "bia", name: "Bia", bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" };
  const musica = {
    id, chave_catalogo: `teste-${id}`, titulo: `Música ${id}`, artista: "Artista",
    tipo_versao: "ao_vivo", descricao_versao: "Show de teste", generos: [], tags: [], capa_url: "",
  };
  return { id, texto: "ok", nota: 8, tem_texto: true, musica, autor, created_at: "2026-11-24T10:00:00Z" };
}

const pagina = (route: Route, ids: number[], total: number) =>
  route.fulfill({ json: { items: ids.map(review), total, offset: 0, limit: 10 } });

const ehFeed = (url: URL) => url.port === "8000" && url.pathname === "/feed";

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`feed_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

const abrirFeed = (page: Page) => page.getByRole("link", { name: "Feed", exact: true }).click();

test("carrega mais sem repetir e atualizar recomeça a lista", async ({ page }) => {
  await entrar(page);
  await page.route(ehFeed, (route) => {
    const offset = new URL(route.request().url()).searchParams.get("offset");
    return offset === "0" ? pagina(route, [3, 2], 4) : pagina(route, [2, 1], 4);
  });
  await abrirFeed(page);
  await expect(page.getByRole("article")).toHaveCount(2);
  await expect(page.getByRole("article").first()).toContainText("Ao vivo · Show de teste");
  await page.getByRole("button", { name: "Carregar mais" }).click();
  await expect(page.getByRole("article")).toHaveCount(3);
  await expect(page.getByRole("button", { name: "Carregar mais" })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Atualizar" }).click();
  await expect(page.getByRole("article")).toHaveCount(2);
});

test("falha na próxima página mantém os itens e permite repetir", async ({ page }) => {
  await entrar(page);
  let falhar = true;
  await page.route(ehFeed, (route) => {
    const offset = new URL(route.request().url()).searchParams.get("offset");
    if (offset === "0") return pagina(route, [2], 2);
    return falhar ? route.abort() : pagina(route, [1], 2);
  });
  await abrirFeed(page);
  await page.getByRole("button", { name: "Carregar mais" }).click();
  await expect(page.getByText("Não foi possível conectar.", { exact: false })).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(1);
  falhar = false;
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(page.getByRole("article")).toHaveCount(2);
});

test("estado vazio e servidor sem a rota do feed", async ({ page }) => {
  await entrar(page);
  await page.route(ehFeed, (route) => pagina(route, [], 0));
  await abrirFeed(page);
  await expect(page.getByText("Nenhuma review por aqui ainda.", { exact: false })).toBeVisible();
  // O servidor real já tem o /feed; um servidor sem a rota responde 404, então simulamos isso.
  await page.unroute(ehFeed);
  await page.route(ehFeed, (route) => route.fulfill({ status: 404, json: { detail: "Not Found" } }));
  await page.getByRole("button", { name: "Atualizar" }).click();
  await expect(page.getByText("O feed ainda não está disponível neste servidor.")).toBeVisible();
});
