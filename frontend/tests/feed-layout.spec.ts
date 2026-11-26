import { expect, test, type Page, type Route } from "@playwright/test";

const musica = {
  id: 1, chave_catalogo: "teste-1", titulo: "Maré", artista: "Faroleiros",
  tipo_versao: "original", descricao_versao: "", generos: [], tags: [], capa_url: "",
};
const autor = { id: 99, username: "bia", name: "Bia", bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" };
// Sem sufixo de fuso, como o backend envia.
const haDozeMinutos = () => new Date(Date.now() - 12 * 60_000).toISOString().replace("Z", "");

const naApi = (caminho: string) => (url: URL) => url.port === "8000" && url.pathname === caminho;
const pagina = (items: object[]) => ({ json: { items, total: items.length, offset: 0, limit: 10 } });

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa Ouvinte");
  await page.getByLabel("Usuário", { exact: true }).fill(`layout_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

test("três colunas no computador e atalhos no celular", async ({ page }, info) => {
  await entrar(page);
  const post = { id: 7, texto: "ok", nota: 9, tem_texto: true, musica, autor, created_at: haDozeMinutos(), curtidas: 12, curtido_por_mim: false };
  await page.route(naApi("/feed"), (route) => route.fulfill(pagina([post])));
  await page.route(naApi("/musicas/populares"), (route) => route.fulfill(pagina([{ ...musica, quantidade_reviews: 24 }])));
  await page.getByRole("link", { name: "Feed", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Seu feed" })).toBeVisible();
  await expect(page.getByRole("article")).toContainText("há 12 min");
  const largo = (page.viewportSize()?.width ?? 0) >= 1024;
  await expect(page.getByText("Mais avaliadas na comunidade")).toBeVisible({ visible: largo });
  await expect(page.getByText("Ver meu perfil")).toBeVisible({ visible: largo });
  await expect(page.getByText("Pesquisar músicas")).toBeVisible({ visible: !largo });
  if (largo) await expect(page.getByText("24 reviews")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("feed.png"), fullPage: true });
});

test("pesquisa abre a página da música e falha lateral não bloqueia o feed", async ({ page }) => {
  await entrar(page);
  await page.route(naApi("/feed"), (route) => route.fulfill(pagina([])));
  // O servidor real já tem estas rotas; um servidor sem elas responde 404, então simulamos a falha lateral.
  const semRota = (route: Route) => route.fulfill({ status: 404, json: { detail: "Not Found" } });
  await page.route(naApi("/musicas/populares"), semRota);
  await page.route((url) => url.port === "8000" && /^\/musicas\/\d+\/reviews$/.test(url.pathname), semRota);
  await page.goto("/musicas");
  await expect(page.getByText("mais avaliadas ainda não estão disponíveis", { exact: false })).toBeVisible();
  await page.getByLabel("Buscar música ou artista").fill("mare");
  await page.getByRole("link", { name: /Lua de Barro/ }).click();
  await expect(page.getByRole("heading", { name: "Maré" })).toBeVisible();
  await expect(page.getByText("As reviews desta música ainda não estão disponíveis neste servidor.")).toBeVisible();
  await page.getByRole("link", { name: "Feed", exact: true }).click();
  await expect(page.getByText("Nenhuma review por aqui ainda.", { exact: false })).toBeVisible();
});

test("compartilhar copia o link da review", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.addInitScript(() => Object.defineProperty(navigator, "share", { value: undefined }));
  await entrar(page);
  const post = { id: 7, texto: "", nota: 9, tem_texto: false, musica, autor, created_at: haDozeMinutos() };
  await page.route(naApi("/feed"), (route) => route.fulfill(pagina([post])));
  await page.getByRole("link", { name: "Feed", exact: true }).click();
  await page.getByRole("button", { name: "Compartilhar review" }).click();
  await expect(page.getByText("Link copiado.")).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe("http://localhost:3000/posts/7");
});
