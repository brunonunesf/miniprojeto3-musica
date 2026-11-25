import { expect, test, type Page } from "@playwright/test";

const autor = { id: 99, username: "bia", name: "Bia", bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" };
const musica = {
  id: 1, chave_catalogo: "teste-1", titulo: "Maré", artista: "Faroleiros",
  tipo_versao: "original", descricao_versao: "", generos: [], tags: [], capa_url: "",
};
const base = { id: 7, texto: "", nota: 7, tem_texto: false, musica, autor, created_at: autor.created_at };

const naApi = (caminho: string) => (url: URL) => url.port === "8000" && url.pathname === caminho;

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`curtir_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

const comFeed = (page: Page, post: object) =>
  page.route(naApi("/feed"), (route) => route.fulfill({ json: { items: [post], total: 1, offset: 0, limit: 10 } }));

test("curtir e descurtir usam a contagem do servidor e a falha não a altera", async ({ page }) => {
  await entrar(page);
  await comFeed(page, { ...base, curtidas: 2, curtido_por_mim: false });
  let falhar = false;
  let envios = 0;
  let liberar = () => {};
  const espera = new Promise<void>((resolve) => (liberar = resolve));
  await page.route(naApi("/posts/7/curtir"), async (route) => {
    const metodo = route.request().method();
    if (metodo === "OPTIONS") return route.fallback();
    envios++;
    if (falhar) return route.abort();
    await espera;
    const curtiu = metodo === "POST";
    // 5 e não 3: outras pessoas curtiram no intervalo.
    return route.fulfill({ json: { curtidas: curtiu ? 5 : 1, curtido_por_mim: curtiu } });
  });

  await page.getByRole("link", { name: "Feed", exact: true }).click();
  await expect(page.getByText("2 curtidas")).toBeVisible();
  await page.getByRole("button", { name: "Curtir", exact: true }).click();
  await expect(page.getByRole("button", { name: "Enviando…" })).toBeDisabled();
  liberar();
  await expect(page.getByText("5 curtidas")).toBeVisible();
  expect(envios).toBe(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  falhar = true;
  await page.getByRole("button", { name: "Descurtir" }).click();
  await expect(page.getByText("Não foi possível conectar.", { exact: false })).toBeVisible();
  await expect(page.getByText("5 curtidas")).toBeVisible();
  await expect(page.getByRole("button", { name: "Descurtir" })).toBeEnabled();
  falhar = false;
  await page.getByRole("button", { name: "Descurtir" }).click();
  await expect(page.getByText("1 curtida", { exact: true })).toBeVisible();

  // Atualizar o feed volta a mostrar o que o servidor informa.
  await page.getByRole("button", { name: "Atualizar" }).click();
  await expect(page.getByText("2 curtidas")).toBeVisible();
});

test("sem curtidas no servidor não há botão", async ({ page }) => {
  await entrar(page);
  await comFeed(page, base);
  await page.getByRole("link", { name: "Feed", exact: true }).click();
  await expect(page.getByRole("article")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Curtir", exact: true })).toHaveCount(0);
});
