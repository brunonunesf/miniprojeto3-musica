import { createHmac } from "node:crypto";
import { expect, test, type Page } from "@playwright/test";

const chave = "chave-exclusiva-dos-testes-playwright-32";

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa do catálogo");
  await page.getByLabel("Usuário", { exact: true }).fill(`catalogo_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
  return page.evaluate(async () => {
    const headers = { Authorization: `Bearer ${localStorage.getItem("token")}` };
    return (await fetch("http://localhost:8000/auth/eu", { headers })).json();
  });
}

test("seleção externa só persiste ao publicar e exibe fonte indisponível", async ({ page }) => {
  const usuario = await entrar(page);
  const id = `ext${Date.now()}`;
  const faixa = { servico: "spotify", id_externo: id, url: `https://open.spotify.com/track/${id}`,
    titulo: `Canção externa ${id}`, artistas: ["Artista externo"], album: "Álbum",
    duracao_ms: 180000, isrc: "BRABC2600001", tipo_versao: "desconhecida", descricao_versao: "", capa_url: null };
  const corpo = Buffer.from(JSON.stringify({ v: 1, usuario: usuario.id, exp: Math.floor(Date.now() / 1000) + 900, faixas: [faixa] })).toString("base64url");
  const token = `${corpo}.${createHmac("sha256", chave).update(corpo).digest("hex")}`;
  // Só a resposta externa é simulada. Publicação, consulta e persistência usam a API real.
  await page.route((u) => u.port === "8000" && u.pathname === "/musicas/busca", (route) => route.fulfill({ json: {
    items: [{ chave: `spotify:${id}`, musica_id: null, selecao_externa: token,
      musica: { titulo: faixa.titulo, artista: "Artista externo", tipo_versao: "desconhecida", descricao_versao: "", capa_url: "", generos: [], tags: [] },
      fontes: ["spotify"], referencias: [{ servico: "spotify", url: faixa.url }] }],
    total_local: 0, fontes: { local: "disponivel", spotify: "disponivel", deezer: "indisponivel" },
  } }));
  await page.goto("/posts/novo");
  await page.getByLabel("Buscar música por título ou artista").fill("externa");
  await page.getByRole("radio", { name: /Artista externo/ }).check();
  await expect(page.getByText("Deezer: temporariamente indisponível.", { exact: false })).toBeVisible();
  await expect(page.getByText("Versão não confirmada", { exact: true })).toBeVisible();
  const pesquisarLocal = () => page.evaluate(async (q) => {
    const res = await fetch(`http://localhost:8000/musicas?q=${encodeURIComponent(q)}`, { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });
    return res.json();
  }, faixa.titulo);
  expect((await pesquisarLocal()).total).toBe(0);
  // Sair do formulário depois de selecionar também não grava.
  await page.goto("/musicas");
  expect((await pesquisarLocal()).total).toBe(0);
  await page.goto("/posts/novo");
  await page.getByLabel("Buscar música por título ou artista").fill("externa");
  await page.getByRole("radio", { name: /Artista externo/ }).check();
  await page.getByLabel("Nota (0 a 10)").selectOption("8");
  await page.getByRole("button", { name: "Publicar review" }).click();
  await expect(page.getByRole("heading", { name: faixa.titulo, exact: true })).toBeVisible();
  expect((await pesquisarLocal()).total).toBe(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("pedido de inclusão fica privado e aparece pendente sem publicar review", async ({ page }) => {
  await entrar(page);
  await page.goto("/posts/novo");
  await page.getByLabel("Buscar música por título ou artista").fill("Faixa inexistente 987654321");
  await page.getByRole("link", { name: "Solicitar inclusão de uma música" }).click();
  await expect(page.getByLabel("Título", { exact: true })).toHaveValue("Faixa inexistente 987654321");
  await page.getByLabel("Artista", { exact: true }).fill("Artista independente");
  await page.getByLabel("Justificativa", { exact: false }).fill("Gravação independente que gostaria de avaliar.");
  await page.getByRole("button", { name: "Solicitar inclusão", exact: true }).click();
  await expect(page.getByText("Pedido recebido.", { exact: false })).toBeVisible();
  await expect(page.getByText("Estado: pendente")).toBeVisible();
  await expect(page.getByRole("link", { name: "Escrever review" })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
