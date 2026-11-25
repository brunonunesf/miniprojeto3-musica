import { expect, test, type Page } from "@playwright/test";

const bia = { id: 999, username: "bia_exemplo", name: "Bia", bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" };
const musica = { id: 1, titulo: "Maré", artista: "Faroleiros", versao: "original", capa_url: "" };
const review = (id: number) => ({ id, texto: "", nota: 7, tem_texto: false, musica, autor: bia, created_at: bia.created_at });

const naApi = (caminho: string) => (url: URL) => url.port === "8000" && url.pathname === caminho;
const rotaPerfil = naApi("/usuarios/bia_exemplo");
const rotaSeguir = naApi("/usuarios/bia_exemplo/follow");
const rotaPosts = naApi("/usuarios/bia_exemplo/posts");

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`seguir_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}

test("seguir atualiza pelo servidor, trava cliques e mantém o estado em falha", async ({ page }) => {
  await entrar(page);
  let sigo = false;
  let falhar = false;
  let envios = 0;
  let liberar = () => {};
  const espera = new Promise<void>((resolve) => (liberar = resolve));
  await page.route(rotaPerfil, (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    return route.fulfill({ json: { ...bia, sigo, seguidores: sigo ? 8 : 7, seguindo: 2 } });
  });
  await page.route(rotaPosts, (route) => route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 10 } }));
  await page.route(rotaSeguir, async (route) => {
    if (route.request().method() === "OPTIONS") return route.fallback();
    envios++;
    if (falhar) return route.abort();
    await espera;
    sigo = route.request().method() === "POST";
    return route.fulfill({ status: 204 });
  });

  await page.goto("/usuarios/bia_exemplo");
  await expect(page.getByText("Nenhuma review publicada ainda.")).toBeVisible();
  await page.getByRole("button", { name: "Seguir", exact: true }).click();
  await expect(page.getByRole("button", { name: "Enviando…" })).toBeDisabled();
  liberar();
  await expect(page.getByRole("button", { name: "Deixar de seguir" })).toBeVisible();
  await expect(page.getByText("8 seguidores")).toBeVisible();
  expect(envios).toBe(1);

  falhar = true;
  await page.getByRole("button", { name: "Deixar de seguir" }).click();
  await expect(page.getByText("Não foi possível conectar.", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Deixar de seguir" })).toBeEnabled();
  await expect(page.getByText("8 seguidores")).toBeVisible();
});

test("reviews do perfil paginadas", async ({ page }) => {
  await entrar(page);
  await page.route(rotaPerfil, (route) => {
    if (route.request().resourceType() !== "fetch") return route.fallback();
    return route.fulfill({ json: bia });
  });
  await page.route(rotaPosts, (route) => {
    const offset = new URL(route.request().url()).searchParams.get("offset");
    return route.fulfill({ json: { items: [review(offset === "0" ? 2 : 1)], total: 2, offset: 0, limit: 10 } });
  });
  await page.goto("/usuarios/bia_exemplo");
  await expect(page.getByRole("article")).toHaveCount(1);
  await page.getByRole("button", { name: "Carregar mais" }).click();
  await expect(page.getByRole("article")).toHaveCount(2);
  // Sem a relação no servidor, não há botão nem contadores inventados.
  await expect(page.getByRole("button", { name: "Seguir", exact: true })).toHaveCount(0);
  await expect(page.getByText("seguidores")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
