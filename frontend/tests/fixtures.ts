import { test as base, expect } from '@playwright/test';

// Portas alternativas preservam os servidores locais. O encaminhamento usa
// HTTP real e só contorna o CORS fixo da porta 3000 no ambiente de teste.
export const test = base.extend({
  context: async ({ context }, use) => {
    if (process.env.E2E_FRONT_PORT && process.env.E2E_BACK_PORT) {
      await context.route(url => url.hostname === "localhost" && ["8000", process.env.E2E_BACK_PORT].includes(url.port), async route => {
        const url = new URL(route.request().url());
        url.port = process.env.E2E_BACK_PORT!;
        const response = await route.fetch({ url: url.toString() });
        await route.fulfill({ response });
      });
    }
    await use(context);
  },
});
export { expect };
