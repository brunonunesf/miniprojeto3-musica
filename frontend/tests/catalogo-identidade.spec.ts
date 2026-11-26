import { resolve } from "node:path";
import type { Post } from "../lib/api";
import { nomeDaVersao } from "../lib/musica";
import { expect, test, type Page } from "@playwright/test";

// Sem mocks: executar separadamente para cada catálogo, com banco descartável.
test("#39 identidade compartilhada e versões distintas na interface", async ({ page, browser }, info) => {
  // Mesma base de resolução do carregador: backend/, inclusive para caminho absoluto.
  const catalogo = resolve(process.cwd(), "../backend", process.env.CATALOGO_MUSICAL_PATH ?? "data/musicas.json");
  const real = catalogo === resolve(process.cwd(), "../backend/data/musicas_demo.json");
  expect([resolve(process.cwd(), "../backend/data/musicas.json"), resolve(process.cwd(), "../backend/data/musicas_demo.json")]).toContain(catalogo);
  const sufixo = Date.now();
  async function cadastrar(p: Page, nome: string) {
    await p.goto("/registro");
    await p.getByLabel("Nome", { exact: true }).fill(nome);
    await p.getByLabel("Usuário", { exact: true }).fill(nome);
    await p.getByLabel("Senha", { exact: true }).fill("senha-forte-123");
    await p.getByRole("button", { name: "Criar conta", exact: true }).click();
    await expect(p.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
  }
  async function publicar(p: Page, indice: number) {
    await p.goto("/posts/novo");
    await p.getByLabel("Buscar música por título ou artista").fill(real ? "Apesar de Você" : "Horizonte");
    await expect(p.getByRole("radio")).toHaveCount(real ? 1 : 5);
    await p.getByRole("radio").nth(indice).check();
    await p.getByLabel("Nota (0 a 10)").selectOption("8");
    const resposta = p.waitForResponse(r => r.url().endsWith("/posts") && r.request().method() === "POST");
    await p.getByRole("button", { name: "Publicar review", exact: true }).click();
    const r = await resposta;
    expect(r.status()).toBe(201);
    const post: Post = await r.json();
    await expect(p).toHaveURL(new RegExp(`/posts/${post.id}$`));
    await expect(p.getByRole("article")).toContainText(post.musica.artista);
    const versoes: Record<string, string> = { original: "Original", remix: "Remix", ao_vivo: "Ao vivo", remaster: "Remaster" };
    await expect(p.getByRole("article")).toContainText(versoes[post.musica.tipo_versao]);
    if (post.musica.descricao_versao) await expect(p.getByRole("article")).toContainText(post.musica.descricao_versao);
    return post;
  }
  await cadastrar(page, `ana39_${sufixo}`);
  const a = await publicar(page, 0);
  const contexto = await browser.newContext();
  const outra = await contexto.newPage();
  await cadastrar(outra, `bia39_${sufixo}`);
  const b = await publicar(outra, 0);
  expect(a.musica.id).toBe(b.musica.id);
  await page.screenshot({ path: info.outputPath("detalhe.png"), fullPage: true });
  const publicacoes = [a];
  if (!real) {
    for (let i = 1; i < 5; i++) publicacoes.push(await publicar(page, i));
    const musicas = publicacoes.map(post => post.musica);
    expect(new Set(musicas.map(m => m.id)).size).toBe(5);
    expect(new Set(musicas.map(m => m.tipo_versao))).toEqual(new Set(["original", "remix", "ao_vivo", "remaster"]));
    expect(new Set(musicas.map(m => m.artista)).size).toBe(2);
  }
  async function conferirCartoes() {
    await expect(outra.getByRole("article")).toHaveCount(publicacoes.length);
    for (const post of publicacoes) {
      const cartao = outra.getByRole("article").filter({ has: outra.locator(`a[href="/posts/${post.id}"]`) });
      await expect(cartao).toHaveCount(1);
      await expect(cartao.getByRole("link", { name: post.musica.titulo, exact: true })).toHaveAttribute("href", `/posts/${post.id}`);
      await expect(cartao).toContainText(post.musica.artista);
      await expect(cartao).toContainText(nomeDaVersao(post.musica));
    }
  }
  await outra.goto(`/usuarios/ana39_${sufixo}`);
  await conferirCartoes();
  await outra.screenshot({ path: info.outputPath("perfil.png"), fullPage: true });
  await outra.getByRole("button", { name: "Seguir", exact: true }).click();
  await expect(outra.getByRole("button", { name: "Deixar de seguir", exact: true })).toBeVisible();
  await outra.goto("/feed");
  await conferirCartoes();
  await outra.screenshot({ path: info.outputPath("feed.png"), fullPage: true });
  await contexto.close();
});
