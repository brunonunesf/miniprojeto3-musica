import { expect, test } from "@playwright/test";

const pessoa = (id: number) => ({ id, username: `pessoa_${id}`, name: `Pessoa ${id}`, bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" });

test("Pessoas lista perfis, pagina, trata falha e não cria conta por fora do cadastro", async ({ page }) => {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`lista_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();

  let falhar = true;
  await page.route((url) => url.port === "8000" && url.pathname === "/usuarios", (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    if (falhar) return route.fulfill({ status: 500, json: {} });
    const offset = Number(new URL(route.request().url()).searchParams.get("offset"));
    return route.fulfill({ json: { items: [pessoa(offset + 1)], total: 2, offset, limit: 20 } });
  });

  await page.goto("/usuarios");
  await expect(page.getByText("O serviço está indisponível.", { exact: false })).toBeVisible();
  falhar = false;
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(page.getByRole("link", { name: /Pessoa 1/ })).toHaveAttribute("href", "/usuarios/pessoa_1");
  await page.getByRole("button", { name: "Mais pessoas" }).click();
  await expect(page.getByRole("link", { name: /Pessoa 2/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Mais pessoas" })).toHaveCount(0);
  await expect(page.getByRole("textbox")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
