import { expect, test, type Page } from "@playwright/test";

const senha = "senha-forte-123";

async function cadastrar(page: Page, username: string, nome: string) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill(nome);
  await page.getByLabel("Usuário", { exact: true }).fill(username);
  await page.getByLabel("Senha", { exact: true }).fill(senha);
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
}

test("ver e editar o próprio perfil atualiza o cabeçalho", async ({ page }) => {
  const username = `perfil_${Date.now()}`;
  await cadastrar(page, username, "Antes");
  await page.getByRole("link", { name: "Antes", exact: true }).click();
  await page.getByRole("button", { name: "Editar perfil" }).click();
  await page.getByLabel("Nome", { exact: true }).fill("Depois");
  await page.getByLabel("Bio").fill("ouvindo de tudo");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByRole("heading", { name: "Depois" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Depois", exact: true })).toBeVisible();
  await expect(page.getByText("ouvindo de tudo")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("resposta atrasada de um perfil não sobrescreve o perfil atual", async ({ page }) => {
  const sufixo = Date.now();
  const lento = `lento_${sufixo}`;
  const rapido = `rapido_${sufixo}`;
  await cadastrar(page, lento, "Perfil Lento");
  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await cadastrar(page, rapido, "Perfil Rapido");

  let liberar = () => {};
  const espera = new Promise<void>((resolve) => (liberar = resolve));
  await page.route(`**/usuarios/${lento}`, async (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    await espera;
    await route.continue();
  });
  await page.getByRole("link", { name: "Conhecer pessoas" }).click();
  await page.locator(`a[href="/usuarios/${lento}"]`).click();
  await expect(page.getByText("Carregando perfil…")).toBeVisible();
  await page.getByRole("link", { name: "Perfil Rapido", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Perfil Rapido" })).toBeVisible();
  const atrasada = page.waitForResponse((r) => r.url().endsWith(`/usuarios/${lento}`) && r.request().resourceType() === "fetch");
  liberar();
  await atrasada;
  await expect(page.getByRole("heading", { name: "Perfil Rapido" })).toBeVisible();
});

test("cadastro recusa username reservado", async ({ page }) => {
  await cadastrar(page, "stats", "Alguém");
  await expect(page.getByText("Esse usuário é reservado. Escolha outro.")).toBeVisible();
});
