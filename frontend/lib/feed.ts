import { ApiError, apiGet, type Page, type Post } from "@/lib/api";
import { EXEMPLOS_DO_FEED } from "@/lib/feedExemplos";

// Ligado só em desenvolvimento, enquanto GET /feed não existe no backend.
export const FEED_SIMULADO = process.env.NEXT_PUBLIC_FEED_SIMULADO === "true";
const TAMANHO_PAGINA = 10;

export async function buscarFeed(offset: number): Promise<Page<Post>> {
  if (FEED_SIMULADO) {
    const items = EXEMPLOS_DO_FEED.slice(offset, offset + TAMANHO_PAGINA);
    return { items, total: EXEMPLOS_DO_FEED.length, offset, limit: TAMANHO_PAGINA };
  }
  try {
    return await apiGet<Page<Post>>(`/feed?offset=${offset}&limit=${TAMANHO_PAGINA}`);
  } catch (falha) {
    if (falha instanceof ApiError && falha.status === 404) {
      throw new ApiError(404, "O feed ainda não está disponível neste servidor.");
    }
    throw falha;
  }
}
