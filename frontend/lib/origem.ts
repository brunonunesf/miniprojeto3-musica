import { apiPatch, type Post } from "@/lib/api";
import { servidorTemRota } from "@/lib/rotas";

/** Resposta da correção: a origem pode estar salva com reputação indisponível. */
export type OrigemCorrigida = Post & { reputacao_disponivel?: boolean };
export function trocarOrigem(postId: number, origemId: number): Promise<OrigemCorrigida> {
  return apiPatch<OrigemCorrigida>(`/posts/${postId}/origem`, { origem_id: origemId });
}

/** A ação só aparece se o servidor publicar a rota. */
export function servidorCorrigeOrigem(): Promise<boolean> {
  return servidorTemRota(/^\/posts\/\{[^}]+\}\/origem$/, "patch");
}
