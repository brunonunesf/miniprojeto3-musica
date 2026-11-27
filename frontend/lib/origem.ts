import { apiGet, apiPatch, type Post } from "@/lib/api";

/**
 * Contrato proposto pelo front (a rota ainda não existe no backend):
 * PATCH /posts/{id}/origem com { origem_id } devolve a review atualizada.
 */
export function trocarOrigem(postId: number, origemId: number): Promise<Post> {
  return apiPatch<Post>(`/posts/${postId}/origem`, { origem_id: origemId });
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
