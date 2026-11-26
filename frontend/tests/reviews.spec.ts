import { expect, test, type Page } from "@playwright/test";

const senha = "senha-forte-123";

async function cadastrar(page: Page, username: string) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa Ouvinte");
  await page.getByLabel("Usuário", { exact: true }).fill(username);
  await page.getByLabel("Senha", { exact: true }).fill(senha);
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

// Faixas do catálogo importado pelo backend (backend/data/musicas.json).
async function preencher(page: Page) {
  await page.goto("/posts/novo");
  await expect(page).toHaveURL(/\/posts\/novo$/);
  await page.getByLabel("Buscar música por título ou artista").fill("mare");
  await expect(page.getByRole("radio")).toHaveCount(1);
  await page.getByRole("radio", { name: /Lua de Barro/ }).check();
  await expect(page.getByRole("status")).toContainText("Lua de Barro");
  await page.getByLabel("Nota (0 a 10)").selectOption("9");
  await page.getByLabel("Sua análise (opcional)").fill("Linda demais.");
}

async function publicar(page: Page) {
  await preencher(page);
  await page.getByRole("button", { name: "Publicar review" }).click();
}

test("publicar, editar e excluir uma review", async ({ page }) => {
  await cadastrar(page, `review_${Date.now()}`);
  await publicar(page);
  await expect(page.getByRole("heading", { name: "Maré" })).toBeVisible();
  await expect(page.getByRole("article")).toContainText("Lua de Barro");
  await expect(page.getByRole("article")).toContainText("Original");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  await page.getByRole("button", { name: "Editar review" }).click();
  await page.getByLabel("Nota (0 a 10)").selectOption("10");
  await page.getByLabel("Sua análise (opcional)").fill("Ainda melhor.");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByRole("button", { name: "Editar review" })).toBeVisible();
  await expect(page.getByRole("article")).toContainText("Ainda melhor.");
  await expect(page.getByRole("article")).toContainText("10/10");

  const endereco = page.url();
  await page.getByRole("button", { name: "Excluir", exact: true }).click();
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  await expect(page).toHaveURL("http://localhost:3000/");
  await page.goto(endereco);
  await expect(page.getByText("post não encontrado")).toBeVisible();
});

test("review repetida preserva o formulário e outra pessoa não edita", async ({ page }) => {
  const sufixo = `${Date.now()}`;
  await cadastrar(page, `autora_${sufixo}`);
  await publicar(page);
  await expect(page.getByRole("heading", { name: "Maré" })).toBeVisible();
  const endereco = page.url();
  await publicar(page);
  await expect(page.getByText("você já fez uma review desta música")).toBeVisible();
  await expect(page.getByLabel("Sua análise (opcional)")).toHaveValue("Linda demais.");
  await expect(page.getByRole("radio", { name: /Lua de Barro/ })).toBeChecked();

  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await cadastrar(page, `leitora_${sufixo}`);
  await page.goto(endereco);
  await expect(page.getByRole("heading", { name: "Maré" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Editar review" })).toHaveCount(0);
});

test("sem música, com música inválida ou sem rede, o formulário é preservado", async ({ page }) => {
  await cadastrar(page, `falha_${Date.now()}`);
  await page.goto("/posts/novo");
  await page.getByLabel("Nota (0 a 10)").selectOption("5");
  await page.getByRole("button", { name: "Publicar review" }).click();
  await expect(page.getByText("Escolha uma música do catálogo.")).toBeVisible();

  await preencher(page);
  const ehPublicacao = (url: URL) => url.port === "8000" && url.pathname === "/posts";
  await page.route(ehPublicacao, (route) => route.abort());
  await page.getByRole("button", { name: "Publicar review" }).click();
  await expect(page.getByText("Não foi possível conectar.", { exact: false })).toBeVisible();
  await expect(page.getByLabel("Sua análise (opcional)")).toHaveValue("Linda demais.");

  await page.unroute(ehPublicacao);
  await page.route(ehPublicacao, (route) =>
    route.fulfill({ status: 422, json: { detail: "música não encontrada no catálogo" } }),
  );
  await page.getByRole("button", { name: "Publicar review" }).click();
  await expect(page.getByText("música não encontrada no catálogo")).toBeVisible();
  await expect(page.getByLabel("Nota (0 a 10)")).toHaveValue("9");
});

test("busca sem resultado e catálogo indisponível", async ({ page }) => {
  await cadastrar(page, `busca_${Date.now()}`);
  await page.goto("/posts/novo");
  const busca = page.getByLabel("Buscar música por título ou artista");
  await busca.fill("nada parecido");
  await expect(page.getByText("Nenhuma música encontrada no catálogo.")).toBeVisible();
  const ehCatalogo = (url: URL) => url.port === "8000" && url.pathname === "/musicas";
  await page.route(ehCatalogo, (route) => route.abort());
  await busca.fill("horizonte");
  await expect(page.getByText("Não foi possível conectar.", { exact: false })).toBeVisible();
  await page.unroute(ehCatalogo);
  await page.getByRole("button", { name: "Buscar de novo" }).click();
  await expect(page.getByRole("radio")).toHaveCount(5);
});
