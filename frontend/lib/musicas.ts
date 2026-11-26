import { ApiError, apiGet, type Musica, type Page, type Post } from "@/lib/api";
import { FEED_SIMULADO } from "@/lib/feed";
import { EXEMPLOS_DO_FEED } from "@/lib/feedExemplos";

export type MusicaPopular = Musica & { quantidade_reviews: number };

const TAMANHO_PAGINA = 10;

/** Troca o 404 de uma rota que o servidor ainda não tem por uma explicação. */
async function comAviso<T>(pedido: Promise<T>, aviso: string, semRota = [404]): Promise<T> {
  try {
    return await pedido;
  } catch (falha) {
    if (falha instanceof ApiError && semRota.includes(falha.status)) throw new ApiError(404, aviso);
    throw falha;
  }
}

export async function buscarPopulares(offset: number, limit: number): Promise<Page<MusicaPopular>> {
  if (FEED_SIMULADO) {
    const exemplos = EXEMPLOS_DO_FEED.slice(0, 4).map((post, i) => ({ ...post.musica, quantidade_reviews: 24 - i * 5 }));
    return { items: exemplos.slice(offset, offset + limit), total: exemplos.length, offset, limit };
  }
  return comAviso(
    apiGet<Page<MusicaPopular>>(`/musicas/populares?offset=${offset}&limit=${limit}`),
    "As músicas mais avaliadas ainda não estão disponíveis neste servidor.",
    // Sem a rota, "populares" é lido como id de música e o servidor responde 422.
    [404, 422],
  );
}

export function buscarReviewsDaMusica(musicaId: string, offset: number): Promise<Page<Post>> {
  return comAviso(
    apiGet<Page<Post>>(`/musicas/${encodeURIComponent(musicaId)}/reviews?offset=${offset}&limit=${TAMANHO_PAGINA}`),
    "As reviews desta música ainda não estão disponíveis neste servidor.",
  );
}
