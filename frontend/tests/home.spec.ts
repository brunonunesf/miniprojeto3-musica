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
