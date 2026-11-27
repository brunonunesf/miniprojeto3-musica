import { apiGet } from "@/lib/api";

/**
 * Pergunta ao servidor se ele publica uma rota, para não oferecer o que falharia.
 * Nos padrões, cada parâmetro do caminho aparece como `{...}`.
 */
export async function servidorTemRota(caminho: RegExp, metodo: "get" | "post" | "patch"): Promise<boolean> {
  try {
    const { paths } = await apiGet<{ paths?: Record<string, object> }>("/openapi.json");
    return Object.entries(paths ?? {}).some(([rota, metodos]) => caminho.test(rota) && metodo in metodos);
  } catch {
    return false;
  }
}
