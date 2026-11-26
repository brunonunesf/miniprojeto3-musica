import { expect, test, type Page } from "@playwright/test";

const musica = {
  id: 1, chave_catalogo: "teste-1", titulo: "Maré", artista: "Faroleiros",
  tipo_versao: "original", descricao_versao: "", generos: [], tags: [], capa_url: "",
};
type No = { id: number; apagada: boolean; autor: { username: string; name: string } | null; nota: number | null; filhos: No[] };
const no = (id: number, name: string, filhos: No[] = []): No =>
  ({ id, apagada: false, autor: { username: `u${id}`, name }, nota: 8, filhos });

const ehArvore = (url: URL) => url.port === "8000" && /^\/posts\/\d+\/arvore$/.test(url.pathname);

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`arvore_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

test("mostra raiz, ramos, caminho da descoberta e origem apagada sem conteúdo", async ({ page }) => {
  await entrar(page);
  // O nó apagado chega com conteúdo de propósito: a tela não pode mostrá-lo.
  const apagado = { ...no(4, "Nome Secreto", [no(5, "Caio")]), apagada: true };
  const raiz = no(1, "Ana", [no(2, "Júlia", [no(3, "Pedro")]), apagado]);
  await page.route(ehArvore, (route) => route.fulfill({ json: { musica, raiz } }));

  await page.goto("/posts/3/arvore");
  await expect(page.getByText("Descoberta via Júlia ← Ana")).toBeVisible();
  await expect(page.locator('[aria-current="true"]')).toContainText("Pedro");
  await expect(page.getByText("Esta review não existe mais")).toBeVisible();
  await expect(page.getByText("Nome Secreto")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Caio" })).toBeVisible();

  await page.goto("/posts/5/arvore");
  await expect(page.getByText("Descoberta via review apagada ← Ana")).toBeVisible();
});

test("corrente longa cabe na tela", async ({ page }) => {
  await entrar(page);
  let raiz = no(20, "Pessoa com um nome bem comprido 20");
  for (let id = 19; id >= 1; id--) raiz = no(id, `Pessoa com um nome bem comprido ${id}`, [raiz]);
  await page.route(ehArvore, (route) => route.fulfill({ json: { musica, raiz } }));
  await page.goto("/posts/20/arvore");
  await expect(page.locator('[aria-current="true"]')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("árvore isolada e servidor sem a rota", async ({ page }) => {
  await entrar(page);
  await page.route(ehArvore, (route) => route.fulfill({ json: { musica, raiz: no(1, "Ana") } }));
  await page.goto("/posts/1/arvore");
  await expect(page.getByText("Ninguém recomendou a partir desta review ainda.")).toBeVisible();
  await expect(page.getByText("Descoberta via", { exact: false })).toHaveCount(0);
  await page.unroute(ehArvore);
  await page.reload();
  await expect(page.getByText("Árvore não encontrada.", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tentar novamente" })).toBeVisible();
});
