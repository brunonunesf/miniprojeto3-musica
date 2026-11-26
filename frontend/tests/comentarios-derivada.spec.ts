import { expect, test, type Page } from "@playwright/test";

const autor = { id: 99, username: "bia", name: "Bia", bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" };
const musica = {
  id: 1, chave_catalogo: "teste-1", titulo: "Maré", artista: "Faroleiros",
  tipo_versao: "original", descricao_versao: "", generos: [], tags: [], capa_url: "",
};
const review = { id: 7, texto: "Ótima.", nota: 7, tem_texto: true, musica, autor, created_at: autor.created_at };
const comentario = (id: number, texto: string) => ({ id, post_id: 7, texto, autor, created_at: autor.created_at });

const naApi = (caminho: string) => (url: URL) => url.port === "8000" && url.pathname === caminho;

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`conversa_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

const comReview = (page: Page, extra: object) =>
  page.route(naApi("/posts/7"), (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    return route.fulfill({ json: { ...review, ...extra } });
  });

test("comentar preserva o texto em falha e insere uma única vez", async ({ page }) => {
  await entrar(page);
  await comReview(page, { comentarios: 1 });
  let falhar = true;
  let envios = 0;
  await page.route(naApi("/posts/7/comentarios"), (route) => {
    const metodo = route.request().method();
    if (metodo === "OPTIONS") return route.fallback();
    if (metodo === "GET") return route.fulfill({ json: { items: [comentario(1, "Primeiro")], total: 1, offset: 0, limit: 20 } });
    envios++;
    return falhar ? route.abort() : route.fulfill({ status: 201, json: comentario(2, "Segundo") });
  });

  await page.goto("/posts/7");
  await expect(page.getByRole("list", { name: "Conversa" }).getByRole("listitem")).toHaveCount(1);
  await page.getByRole("button", { name: "Comentar", exact: true }).click();
  await expect(page.getByText("Escreva o comentário.")).toBeVisible();
  await page.getByLabel("Seu comentário").fill("Segundo");
  await page.getByRole("button", { name: "Comentar", exact: true }).click();
  await expect(page.getByText("Não foi possível conectar.", { exact: false })).toBeVisible();
  await expect(page.getByLabel("Seu comentário")).toHaveValue("Segundo");
  falhar = false;
  await page.getByRole("button", { name: "Comentar", exact: true }).click();
  await expect(page.getByRole("list", { name: "Conversa" }).getByRole("listitem")).toHaveCount(2);
  await expect(page.getByLabel("Seu comentário")).toHaveValue("");
  expect(envios).toBe(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("review derivada envia a origem, exige análise e trata repetida", async ({ page }) => {
  await entrar(page);
  await comReview(page, { origem_id: null });
  let corpo: Record<string, unknown> = {};
  await page.route(naApi("/posts"), (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    corpo = route.request().postDataJSON();
    return route.fulfill({ status: 409, json: { detail: "você já fez uma review desta música" } });
  });
  await page.goto("/posts/7");
  await page.getByRole("link", { name: "Escrever review a partir desta" }).click();
  await expect(page.getByRole("heading", { name: "Nova review derivada" })).toBeVisible();
  await expect(page.getByText("A partir da review de Bia")).toBeVisible();
  await expect(page.getByRole("radio")).toHaveCount(0);
  await page.getByLabel("Nota (0 a 10)").selectOption("9");
  await page.getByRole("button", { name: "Publicar review" }).click();
  await expect(page.getByText("A review derivada precisa da sua própria análise.")).toBeVisible();
  await page.getByLabel("Sua análise (obrigatória)").fill("Minha opinião.");
  await page.getByRole("button", { name: "Publicar review" }).click();
  await expect(page.getByRole("link", { name: "Ver minhas reviews" })).toBeVisible();
  await expect(page.getByLabel("Sua análise (obrigatória)")).toHaveValue("Minha opinião.");
  expect(corpo).toEqual({ musica_id: 1, nota: 9, texto: "Minha opinião.", origem_id: 7 });
});

test("servidor sem review derivada não oferece nem publica a ligação", async ({ page }) => {
  await entrar(page);
  await comReview(page, {});
  await page.goto("/posts/7");
  await expect(page.getByRole("button", { name: /Escrever review a partir desta/ })).toBeDisabled();
  await expect(page.getByRole("heading", { name: "Comentários" })).toHaveCount(0);
  await page.goto("/posts/novo?origem=7");
  await expect(page.getByText("Este servidor ainda não aceita review derivada.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Publicar review" })).toHaveCount(0);
});

test("derivada repetida leva à review existente, sem trocar a origem", async ({ page }) => {
  const publicar = async () => {
    await page.getByLabel("Nota (0 a 10)").selectOption("8");
    await page.getByLabel(/Sua análise/).fill("Minha opinião.");
    await page.getByRole("button", { name: "Publicar review" }).click();
  };
  await entrar(page);
  await page.goto("/posts/novo");
  await page.getByRole("radio", { name: /Trio Ventania/ }).check();
  await publicar();
  await expect(page).toHaveURL(/\/posts\/\d+$/);
  const origem = page.url();

  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await entrar(page);
  await page.goto("/posts/novo");
  await page.getByRole("radio", { name: /Trio Ventania/ }).check();
  await publicar();
  await expect(page).toHaveURL(/\/posts\/\d+$/);
  const independente = page.url();

  await page.goto(origem);
  await page.getByRole("link", { name: "Escrever review a partir desta" }).click();
  await publicar();
  await expect(page.getByText("você já fez uma review desta música")).toBeVisible();
  await page.getByRole("link", { name: "Abrir a sua review desta música" }).click();
  await expect(page).toHaveURL(independente);
  await expect(page.getByText("A partir da review de", { exact: false })).toHaveCount(0);
});
