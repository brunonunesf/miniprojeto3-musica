import { defineConfig, devices } from "@playwright/test";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const banco = join(mkdtempSync(join(tmpdir(), "musica-e2e-")), "test.db");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  use: { baseURL: "http://localhost:3000", channel: process.env.PLAYWRIGHT_CHANNEL, trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Desktop Chrome"], viewport: { width: 360, height: 800 } } },
  ],
  webServer: [
    {
      command: "../backend/.venv/bin/python -m uvicorn app.main:app --app-dir ../backend --port 8000",
      url: "http://localhost:8000/docs",
      env: { DATABASE_URL: `sqlite:///${banco}`, DEBUG: "false", MUSICA_SELECTION_SECRET: "chave-exclusiva-dos-testes-playwright-32", SPOTIFY_BUSCA_VALIDADA: "false", DEEZER_BUSCA_VALIDADA: "false" },
      reuseExistingServer: false,
    },
    {
      command: "npm run start -- --port 3000",
      url: "http://localhost:3000/login",
      env: { NEXT_PUBLIC_API_URL: "http://localhost:8000" },
      reuseExistingServer: false,
    },
  ],
});
