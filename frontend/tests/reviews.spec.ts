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

async function publicar(page: Page, titulo: string) {
  await page.getByRole("link", { name: "Nova review", exact: true }).click();
  await expect(page).toHaveURL(/\/posts\/novo$/);
  await page.getByLabel("Título da música").fill(titulo);
  await page.getByLabel("Artista").fill("Elis Regina");
  await page.getByLabel("Nota (0 a 10)").selectOption("9");
  await page.getByLabel("Sua análise (opcional)").fill("Linda demais.");
  await page.getByRole("button", { name: "Publicar review" }).click();
}

test("publicar, editar e excluir uma review", async ({ page }) => {
  const sufixo = `${Date.now()}`;
  await cadastrar(page, `review_${sufixo}`);
  await publicar(page, `Águas ${sufixo}`);
  await expect(page.getByRole("heading", { name: `Águas ${sufixo}` })).toBeVisible();
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
  await publicar(page, `Repetida ${sufixo}`);
  await expect(page.getByRole("heading", { name: `Repetida ${sufixo}` })).toBeVisible();
  const endereco = page.url();
  await publicar(page, `Repetida ${sufixo}`);
  await expect(page.getByText("você já fez uma review desta música")).toBeVisible();
  await expect(page.getByLabel("Sua análise (opcional)")).toHaveValue("Linda demais.");

  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await cadastrar(page, `leitora_${sufixo}`);
  await page.goto(endereco);
  await expect(page.getByRole("heading", { name: `Repetida ${sufixo}` })).toBeVisible();
  await expect(page.getByRole("button", { name: "Editar review" })).toHaveCount(0);
});
