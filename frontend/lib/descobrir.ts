import { ApiError, apiGet, type Page, type Post } from "@/lib/api";
import { EXEMPLOS_DO_FEED } from "@/lib/feedExemplos";

/**
 * Contrato proposto pelo front (a rota ainda não existe no backend):
 * GET /descobrir?offset&limit devolve itens { review, explicacao } e `personalizada`,
 * falso enquanto a conta não tem reviews nem curtidas.
 */
type Resposta = Page<{ review: Post; explicacao: string }> & { personalizada: boolean };
export type Sugestao = Post & { explicacao: string };
export type PaginaDeSugestoes = Page<Sugestao> & { personalizada: boolean };

// Ligado só em desenvolvimento, para ver a tela sem o serviço de sugestões.
export const DESCOBRIR_SIMULADO = process.env.NEXT_PUBLIC_DESCOBRIR_SIMULADO === "true";
const TAMANHO_PAGINA = 10;

export async function buscarSugestoes(offset: number): Promise<PaginaDeSugestoes> {
  if (DESCOBRIR_SIMULADO) {
    const items = EXEMPLOS_DO_FEED.slice(offset, offset + TAMANHO_PAGINA).map((post) => ({
      ...post,
      explicacao: "Motivo de exemplo: gênero em comum com músicas que você avaliou.",
    }));
    return { items, total: EXEMPLOS_DO_FEED.length, offset, limit: TAMANHO_PAGINA, personalizada: true };
  }
  const pagina = await apiGet<Resposta>(`/descobrir?offset=${offset}&limit=${TAMANHO_PAGINA}`);
  return { ...pagina, items: pagina.items.map(({ review, explicacao }) => ({ ...review, explicacao })) };
}

/** Servidor sem a rota: a tela explica, em vez de mostrar erro. */
export function descobrirIndisponivel(falha: unknown): boolean {
  return falha instanceof ApiError && falha.status === 404;
}
