import { apiGet, apiPatch, type Post } from "@/lib/api";

/** Resposta da correção: a origem pode estar salva com reputação indisponível. */
export type OrigemCorrigida = Post & { reputacao_disponivel?: boolean };
export function trocarOrigem(postId: number, origemId: number): Promise<OrigemCorrigida> {
  return apiPatch<OrigemCorrigida>(`/posts/${postId}/origem`, { origem_id: origemId });
}

/** A ação só aparece se o servidor publicar a rota, para não oferecer o que falharia. */
export async function servidorCorrigeOrigem(): Promise<boolean> {
  try {
    const { paths } = await apiGet<{ paths?: Record<string, object> }>("/openapi.json");
    return Object.entries(paths ?? {}).some(
      ([caminho, metodos]) => /^\/posts\/\{[^}]+\}\/origem$/.test(caminho) && "patch" in metodos,
    );
  } catch {
    return false;
  }
}
