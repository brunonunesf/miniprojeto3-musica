import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

// Cada execução Playwright inicia seus servidores e um banco descartável próprio.
for (const [cenario, catalogo] of [["tecnico", "data/musicas.json"], ["real", "data/musicas_demo.json"]]) {
  console.log(`Validando catálogo ${cenario}: ${catalogo}`);
  const resultado = spawnSync(process.execPath, ["node_modules/@playwright/test/cli.js", "test", "tests/catalogo-identidade.spec.ts", "--project=desktop", `--output=test-results/issue39-${cenario}`], {
    cwd: fileURLToPath(new URL("../", import.meta.url)),
    env: { ...process.env, CATALOGO_MUSICAL_PATH: catalogo },
    stdio: "inherit",
  });
  if (resultado.error) throw resultado.error;
  if (resultado.status !== 0) process.exit(resultado.status ?? 1);
}
