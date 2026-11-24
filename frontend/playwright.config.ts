import { defineConfig, devices } from "@playwright/test";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const frontPort = process.env.E2E_FRONT_PORT ?? "3000";
const backPort = process.env.E2E_BACK_PORT ?? "8000";

const banco = join(mkdtempSync(join(tmpdir(), "musica-e2e-")), "test.db");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  use: { baseURL: `http://localhost:${frontPort}`, channel: process.env.PLAYWRIGHT_CHANNEL, trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Desktop Chrome"], viewport: { width: 360, height: 800 } } },
  ],
  webServer: [
    {
      command: `cd ../backend && .venv/bin/python scripts/seed.py && .venv/bin/python -m uvicorn app.main:app --port ${backPort}`,
      url: `http://localhost:${backPort}/docs`,
      env: { DATABASE_URL: `sqlite:///${banco}`, DEBUG: "false" },
      reuseExistingServer: false,
    },
    {
      command: `npm run start -- --port ${frontPort}`,
      url: `http://localhost:${frontPort}/login`,
      env: { NEXT_PUBLIC_API_URL: `http://localhost:${backPort}` },
      reuseExistingServer: false,
    },
  ],
});
