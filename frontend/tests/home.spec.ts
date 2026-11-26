import { expect, test } from "@playwright/test";

test("visitante vê a home e as páginas privadas continuam protegidas", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "De onde veio essa música?" })).toBeVisible();
  await expect(page).toHaveURL("http://localhost:3000/");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("home.png"), fullPage: true });
  for (const privada of ["/usuarios", "/usuarios/alguem"]) {
    await page.goto(privada);
    await expect(page).toHaveURL(/\/login$/);
  }
});

test("a barra de navegação é a mesma em todas as páginas", async ({ page }) => {
  const medir = async () => {
    const caixa = await page.getByRole("navigation", { name: "Navegação principal" }).boundingBox();
    return [Math.round(caixa!.x), Math.round(caixa!.width), Math.round(caixa!.height)];
  };
  await page.goto("/registro");
  await expect(page.getByRole("link", { name: "Entrar" }).first()).toBeVisible();
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`barra_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
  const referencia = await medir();
  for (const rota of ["/feed", "/descobrir", "/usuarios", "/musicas", "/posts/novo"]) {
    await page.goto(rota);
    await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
    expect(await medir(), rota).toEqual(referencia);
  }
  await page.goto("/usuarios");
  await expect(page.getByRole("link", { name: "Pessoas", exact: true })).toHaveAttribute("aria-current", "page");
});
