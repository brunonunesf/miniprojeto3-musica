import { ApiError, apiGet, type Musica, type User } from "@/lib/api";
import { ARVORE_DE_EXEMPLO } from "@/lib/arvoreExemplo";

export type NoArvore = {
  id: number;
  /** Review excluída: o nó mantém os ramos, mas não mostra autoria nem conteúdo. */
  apagada: boolean;
  autor: Pick<User, "username" | "name"> | null;
  nota: number | null;
  filhos: NoArvore[];
};

export type Arvore = { musica: Musica; raiz: NoArvore; truncada?: boolean };

// Ligado só em desenvolvimento, enquanto o backend não devolve árvores.
export const ARVORE_SIMULADA = process.env.NEXT_PUBLIC_ARVORE_SIMULADA === "true";

export async function buscarArvore(postId: string): Promise<Arvore> {
  if (ARVORE_SIMULADA) return ARVORE_DE_EXEMPLO;
  try {
    return await apiGet<Arvore>(`/posts/${encodeURIComponent(postId)}/arvore`);
  } catch (falha) {
    if (falha instanceof ApiError && falha.status === 404) {
      throw new ApiError(404, "Árvore não encontrada. Ela pode ainda não estar disponível neste servidor.");
    }
    throw falha;
  }
}

/** Nós da raiz até a review pedida; vazio se ela não está na árvore. */
export function caminhoAte(no: NoArvore, id: number): NoArvore[] {
  if (no.id === id) return [no];
  for (const filho of no.filhos) {
    const resto = caminhoAte(filho, id);
    if (resto.length) return [no, ...resto];
  }
  return [];
}

export function nomeNaArvore(no: NoArvore): string {
  return no.apagada || !no.autor ? "review apagada" : no.autor.name;
}
