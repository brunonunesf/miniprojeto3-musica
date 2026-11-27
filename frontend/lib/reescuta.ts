import { apiGet, apiPost, type Page, type Post } from "@/lib/api";
import { servidorTemRota } from "@/lib/rotas";

/**
 * Contrato proposto pelo front (as rotas ainda não existem no backend):
 * - POST /posts/{id}/reescutas com { comentario } cria o aviso; 429 se já houve um nas últimas 24 horas.
 * - GET /feed/reescutas?offset&limit lista os avisos de quem se segue, do mais novo ao mais antigo.
 */
export type Aviso = {
  id: number;
  /** Vazio quando a pessoa não comentou. */
  comentario: string;
  created_at: string;
  /** A review atual mudou depois do aviso. */
  editada: boolean;
  review: Post;
};

export const COMENTARIO_MAXIMO = 1000;
const TAMANHO_PAGINA = 5;

export function servidorAceitaReescuta(): Promise<boolean> {
  return servidorTemRota(/^\/posts\/\{[^}]+\}\/reescutas$/, "post");
}

export function servidorListaReescutas(): Promise<boolean> {
  return servidorTemRota(/^\/feed\/reescutas$/, "get");
}

export function publicarReescuta(postId: number, comentario: string): Promise<Aviso> {
  return apiPost<Aviso>(`/posts/${postId}/reescutas`, { comentario });
}

export function buscarAvisos(offset: number): Promise<Page<Aviso>> {
  return apiGet<Page<Aviso>>(`/feed/reescutas?offset=${offset}&limit=${TAMANHO_PAGINA}`);
}
