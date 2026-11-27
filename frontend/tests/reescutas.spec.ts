import { expect, test, type Page } from "@playwright/test";

const pessoa = (id: number, name: string) => ({ id, username: name.toLowerCase(), name, bio: "", avatar_url: "", created_at: "2026-11-24T10:00:00Z" });
const bia = pessoa(901, "Bia");
const musica = {
  id: 1, chave_catalogo: "teste-1", titulo: "Maré", artista: "Faroleiros",
  tipo_versao: "original", descricao_versao: "", generos: [], tags: [], capa_url: "",
};
const review = (id: number, autor = bia) => ({
  id, texto: "Ótima.", nota: 7, tem_texto: true, musica, autor, created_at: autor.created_at,
  curtidas: 0, curtido_por_mim: false, comentarios: 0, origem_id: null,
});

const naApi = (caminho: string) => (url: URL) => url.port === "8000" && url.pathname === caminho;
const comRotas = (page: Page) =>
  page.route(naApi("/openapi.json"), (route) =>
    route.fulfill({ json: { paths: { "/posts/{post_id}/reescutas": { post: {} }, "/feed/reescutas": { get: {} } } } }),
  );
const semEstouro = (page: Page) => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

async function entrar(page: Page) {
  await page.goto("/registro");
  await page.getByLabel("Nome", { exact: true }).fill("Pessoa");
  await page.getByLabel("Usuário", { exact: true }).fill(`escuta_${Date.now()}`);
  await page.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
  return page.evaluate(async () =>
    (await fetch("http://localhost:8000/auth/eu", { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } })).json(),
  );
}

test("publicar reescuta preserva o comentário no bloqueio e em falha", async ({ page }) => {
  const eu = await entrar(page);
  await comRotas(page);
  await page.route(naApi("/posts/7"), (route) =>
    route.request().resourceType() !== "fetch" ? route.fallback() : route.fulfill({ json: review(7, eu) }),
  );
  let status = 429;
  const bloqueio = "você já avisou desta música; tente de novo em 12 h e 30 min";
  const corpos: unknown[] = [];
  await page.route(naApi("/posts/7/reescutas"), (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    corpos.push(route.request().postDataJSON());
    return status === 201
      ? route.fulfill({ status, json: { id: 1, comentario: "De novo!", created_at: bia.created_at, review: review(7, eu) } })
      : route.fulfill({ status, json: status === 429 ? { detail: bloqueio } : {} });
  });

  await page.goto("/posts/7");
  await page.getByRole("button", { name: "Ouvi novamente" }).click();
  const campo = page.getByLabel("Comentário da reescuta (opcional)");
  await expect(campo).toHaveAttribute("maxlength", "500");
  await campo.fill("  De novo!  ");
  await page.getByRole("button", { name: "Publicar aviso" }).click();
  await expect(page.getByText("tente de novo em 12 h e 30 min", { exact: false })).toBeVisible();
  await expect(campo).toHaveValue("  De novo!  ");
  status = 500;
  await page.getByRole("button", { name: "Publicar aviso" }).click();
  await expect(page.getByText("O serviço está indisponível.", { exact: false })).toBeVisible();
  await expect(campo).toHaveValue("  De novo!  ");
  expect(await semEstouro(page)).toBe(true);
  status = 201;
  await page.getByRole("button", { name: "Publicar aviso" }).click();
  await expect(page.getByText("Aviso publicado para quem segue você.")).toBeVisible();
  await expect(campo).toHaveCount(0);
  expect(corpos).toEqual([{ comentario: "De novo!" }, { comentario: "De novo!" }, { comentario: "De novo!" }]);
});

test("a recusa de review repetida oferece editar ou avisar a reescuta", async ({ page }) => {
  const eu = await entrar(page);
  await comRotas(page);
  await page.route(naApi("/posts"), (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    return route.fulfill({ status: 409, json: { detail: "você já fez uma review desta música" } });
  });
  await page.route(naApi(`/usuarios/${eu.username}/posts`), (route) =>
    route.fulfill({ json: { items: [review(7, eu)], total: 1, offset: 0, limit: 100 } }),
  );
  await page.route(naApi("/musicas"), (route) => route.fulfill({ json: { items: [musica], total: 1, offset: 0, limit: 20 } }));

  await page.goto("/posts/novo");
  await page.getByRole("radio").first().check();
  await page.getByLabel("Nota (0 a 10)").selectOption("8");
  await page.getByRole("button", { name: "Publicar review" }).click();
  await expect(page.getByRole("link", { name: "Abrir a sua review desta música" })).toHaveAttribute("href", "/posts/7");
  await expect(page.getByRole("button", { name: "Ouvi novamente" })).toBeVisible();
});

test("o feed mostra avisos separados, aponta para a review atual e não bloqueia em falha", async ({ page }) => {
  await entrar(page);
  await comRotas(page);
  await page.route(naApi("/feed"), (route) =>
    route.request().resourceType() !== "fetch" ? route.fallback() : route.fulfill({ json: { items: [review(7)], total: 1, offset: 0, limit: 10 } }),
  );
  let falhar = true;
  await page.route(naApi("/feed/reescutas"), (route) => {
    if (falhar) return route.fulfill({ status: 500, json: {} });
    const offset = Number(new URL(route.request().url()).searchParams.get("offset"));
    const aviso = { id: offset + 1, comentario: `Escuta ${offset + 1}`, created_at: bia.created_at, review: review(7) };
    return route.fulfill({ json: { items: [aviso], total: 2, offset, limit: 5 } });
  });

  await page.goto("/feed");
  await expect(page.getByRole("button", { name: "Recarregar avisos" })).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(1);
  falhar = false;
  await page.getByRole("button", { name: "Recarregar avisos" }).click();
  await expect(page.getByText("Escuta 1")).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir a review atual" })).toHaveAttribute("href", "/posts/7");
  await page.getByRole("button", { name: "Mais avisos" }).click();
  await expect(page.getByText("Escuta 2")).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir a review atual" })).toHaveCount(2);
  await page.getByRole("button", { name: "Atualizar" }).click();
  await expect(page.getByText("Escuta 2")).toHaveCount(0);
  await expect(page.getByText("Escuta 1")).toBeVisible();
  expect(await semEstouro(page)).toBe(true);
  await page.screenshot({ path: test.info().outputPath("avisos.png") });
});

test("sem as rotas no servidor, nada de reescuta aparece", async ({ page }) => {
  const eu = await entrar(page);
  await page.route(naApi("/openapi.json"), (route) => route.fulfill({ json: { paths: {} } }));
  await page.route(naApi("/posts/7"), (route) =>
    route.request().resourceType() !== "fetch" ? route.fallback() : route.fulfill({ json: review(7, eu) }),
  );
  const esquema = page.waitForResponse((resposta) => resposta.url().endsWith("/openapi.json"));
  await page.goto("/posts/7");
  await esquema;
  await expect(page.getByRole("button", { name: "Editar review" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ouvi novamente" })).toHaveCount(0);
  await page.goto("/feed");
  await expect(page.getByRole("heading", { name: "Seu feed" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ouvidas novamente" })).toHaveCount(0);
});
