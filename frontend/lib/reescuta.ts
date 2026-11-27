import { apiGet, apiPost, type Page, type Post } from "@/lib/api";
import { servidorTemRota } from "@/lib/rotas";

/** Aviso "ouvi novamente": data e comentário são os do aviso; a review é a de agora. */
export type Aviso = {
  id: number;
  /** Vazio quando a pessoa não comentou. */
  comentario: string;
  created_at: string;
  review: Post;
};

export const COMENTARIO_MAXIMO = 500;
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
