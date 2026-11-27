import { expect, test, type Page } from "@playwright/test";

const bia = { id: 999, username: "bia_exemplo", name: "Bia", bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" };
const musica = {
  id: 1, chave_catalogo: "teste-1", titulo: "Maré", artista: "Faroleiros",
  tipo_versao: "original", descricao_versao: "", generos: [], tags: [], capa_url: "",
};
const review = (id: number) => ({ id, texto: "", nota: 7, tem_texto: false, musica, autor: bia, created_at: bia.created_at });
const naApi = (caminho: string) => (url: URL) => url.port === "8000" && url.pathname === caminho;
const semEstouro = (page: Page) => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

async function entrar(page: Page) {
  const username = `biblio_${Date.now()}`;
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(username);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
  return username;
}

test("a dona muda a visibilidade só com a confirmação do servidor e pagina a lista", async ({ page }) => {
  const eu = await entrar(page);
  let descobertas = "privada";
  let falhar = true;
  const resumo = () => ({
    descobertas: { visibilidade: descobertas, acessivel: true, total: 2 },
    recomendacoes: { visibilidade: "publica", acessivel: true, total: 0 },
  });
  const corpos: unknown[] = [];
  await page.route(naApi(`/usuarios/${eu}/biblioteca`), (route) =>
    route.request().resourceType() !== "fetch" ? route.fallback() : route.fulfill({ json: resumo() }),
  );
  await page.route(naApi(`/usuarios/${eu}/biblioteca/descobertas`), (route) => {
    const offset = Number(new URL(route.request().url()).searchParams.get("offset"));
    return route.fulfill({ json: { items: [review(offset + 1)], total: 2, offset, limit: 10 } });
  });
  await page.route(naApi(`/usuarios/${eu}/biblioteca/recomendacoes`), (route) =>
    route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 10 } }),
  );
  await page.route(naApi("/usuarios/eu/biblioteca"), (route) => {
    if (route.request().method() !== "PATCH") return route.fallback();
    corpos.push(route.request().postDataJSON());
    if (falhar) return route.fulfill({ status: 500, json: {} });
    descobertas = "publica";
    return route.fulfill({ json: resumo() });
  });

  await page.goto(`/usuarios/${eu}`);
  await page.getByRole("link", { name: "Ver biblioteca" }).click();
  await expect(page.getByRole("heading", { name: "Minha biblioteca" })).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(1);
  await page.getByRole("button", { name: "Carregar mais" }).click();
  await expect(page.getByRole("article")).toHaveCount(2);

  const todas = page.getByLabel("Todas as pessoas da rede");
  await todas.click();
  await expect(page.getByText("O serviço está indisponível.", { exact: false })).toBeVisible();
  await expect(page.getByLabel("Só eu")).toBeChecked();
  falhar = false;
  await todas.click();
  await expect(todas).toBeChecked();
  expect(corpos).toEqual([{ descobertas: "publica" }, { descobertas: "publica" }]);

  await page.getByRole("button", { name: "Recomendações (0)" }).click();
  await expect(page.getByText("Nenhuma recomendação própria ainda.")).toBeVisible();
  expect(await semEstouro(page)).toBe(true);
});

test("lista privada de outra pessoa não mostra itens, contagem nem controle", async ({ page }) => {
  await entrar(page);
  let pedidos = 0;
  await page.route(naApi("/usuarios/bia_exemplo/biblioteca"), (route) =>
    route.request().resourceType() !== "fetch"
      ? route.fallback()
      : route.fulfill({
          json: {
            descobertas: { visibilidade: "privada", acessivel: false, total: null },
            recomendacoes: { visibilidade: "publica", acessivel: true, total: 1 },
          },
        }),
  );
  await page.route(naApi("/usuarios/bia_exemplo/biblioteca/descobertas"), (route) => {
    pedidos++;
    return route.fulfill({ status: 403, json: { detail: "esta lista é privada" } });
  });
  await page.route(naApi("/usuarios/bia_exemplo/biblioteca/recomendacoes"), (route) =>
    route.fulfill({ json: { items: [review(1)], total: 1, offset: 0, limit: 10 } }),
  );

  await page.goto("/usuarios/bia_exemplo/biblioteca");
  await expect(page.getByText("Acesso restrito: esta lista é privada.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Descobertas", exact: true })).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(0);
  await expect(page.getByRole("radio")).toHaveCount(0);
  await page.getByRole("button", { name: "Recomendações (1)" }).click();
  await expect(page.getByRole("article")).toHaveCount(1);
  expect(pedidos).toBe(0);
  expect(await semEstouro(page)).toBe(true);
});

test("servidor sem bibliotecas e pessoa inexistente têm avisos próprios", async ({ page }) => {
  await entrar(page);
  let detalhe = "Not Found";
  await page.route(naApi("/usuarios/ninguem/biblioteca"), (route) =>
    route.request().resourceType() !== "fetch" ? route.fallback() : route.fulfill({ status: 404, json: { detail: detalhe } }),
  );
  await page.goto("/usuarios/ninguem/biblioteca");
  await expect(page.getByText("As bibliotecas ainda não estão disponíveis neste servidor.")).toBeVisible();
  detalhe = "usuário não encontrado";
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(page.getByText("usuário não encontrado")).toBeVisible();
});
