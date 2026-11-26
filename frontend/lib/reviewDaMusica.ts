import { apiGet, type Page, type Post } from "@/lib/api";

const TAMANHO_PAGINA = 100;

/** A review da pessoa para a música (há no máximo uma), ou nulo. */
export async function buscarReviewDaMusica(username: string, musicaId: number): Promise<Post | null> {
  const rota = `/usuarios/${encodeURIComponent(username)}/posts`;
  for (let offset = 0; ; offset += TAMANHO_PAGINA) {
    const { items, total } = await apiGet<Page<Post>>(`${rota}?offset=${offset}&limit=${TAMANHO_PAGINA}`);
    const achada = items.find((post) => post.musica.id === musicaId);
    if (achada) return achada;
    if (items.length === 0 || offset + items.length >= total) return null;
  }
}
