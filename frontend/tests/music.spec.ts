import { expect, test } from '@playwright/test';

test('catálogo real: busca, versões, seleção por teclado, vazio e recuperação de erro', async ({ page }) => {
  // Portas isoladas preservam os servidores locais. O CORS de produção continua
  // restrito à porta 3000; o encaminhamento abaixo só existe no teste isolado.
  if (process.env.E2E_FRONT_PORT) {
    await page.route(`http://localhost:${process.env.E2E_BACK_PORT}/**`, async route => {
      const response = await route.fetch();
      await route.fulfill({ response });
    });
  }
  await page.goto('/login');
  await page.getByLabel('Usuário', { exact: true }).fill('ana');
  await page.getByLabel('Senha', { exact: true }).fill('senha-forte-123');
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await page.getByRole('link', { name: 'Músicas', exact: true }).click();
  await expect(page.getByText('6 músicas encontradas')).toBeVisible();
  await expect(page.getByRole('button', { name: /Horizonte — Aurora do Vale/ })).toHaveCount(4);
  const remix = page.getByRole('button', { name: /Horizonte — Aurora do Vale Remix/ });
  await remix.focus();
  await page.keyboard.press('Enter');
  await expect(remix).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByRole('status').filter({ hasText: 'Música selecionada' })).toContainText('Remix de Maré');
  await page.getByLabel('Título ou artista').fill('lua MARÉ');
  await page.getByRole('button', { name: 'Buscar', exact: true }).click();
  await expect(page.getByText('1 músicas encontradas')).toBeVisible();
  await expect(page.getByRole('button', { name: /Maré — Lua de Barro/ })).toBeVisible();
  await page.getByLabel('Título ou artista').fill('inexistente');
  await page.getByRole('button', { name: 'Buscar', exact: true }).click();
  await expect(page.getByText(/Nenhuma música encontrada/)).toBeVisible();
  await page.route('**/musicas?**', route => route.fulfill({ status: 500, body: '{}' }));
  await page.getByLabel('Título ou artista').fill('Horizonte');
  await page.getByRole('button', { name: 'Buscar', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Selecionar música' }).getByRole('alert')).toContainText('indisponível');
  await expect(page.getByLabel('Título ou artista')).toHaveValue('Horizonte');
  await page.unroute('**/musicas?**');
  await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click();
  await expect(page.getByText('5 músicas encontradas')).toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'Música selecionada' })).toContainText('Remix de Maré');
  await page.screenshot({ path: `test-results/catalogo-${test.info().project.name}.png`, fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
