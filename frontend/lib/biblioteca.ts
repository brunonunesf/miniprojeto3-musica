import { ApiError, apiGet, apiPatch, type Page, type Post } from "@/lib/api";

export const LISTAS = [
  { chave: "descobertas", nome: "Descobertas", vazia: "Nenhuma descoberta por indicação ainda." },
  { chave: "recomendacoes", nome: "Recomendações", vazia: "Nenhuma recomendação própria ainda." },
] as const;

export type Lista = (typeof LISTAS)[number]["chave"];
export type Visibilidade = "privada" | "publica";
/** Numa lista restrita a quem pede, `total` é nulo: nem a contagem é revelada. */
export type ResumoDaLista = { visibilidade: Visibilidade; acessivel: boolean; total: number | null };
export type Biblioteca = Record<Lista, ResumoDaLista>;

const TAMANHO_PAGINA = 10;
const rota = (username: string) => `/usuarios/${encodeURIComponent(username)}/biblioteca`;

export async function buscarBiblioteca(username: string): Promise<Biblioteca> {
  try {
    return await apiGet<Biblioteca>(rota(username));
  } catch (falha) {
    // "Not Found" é a rota que não existe; pessoa inexistente vem com outra mensagem.
    if (falha instanceof ApiError && falha.status === 404 && falha.message === "Not Found") {
      throw new ApiError(404, "As bibliotecas ainda não estão disponíveis neste servidor.");
    }
    throw falha;
  }
}

export function buscarItens(username: string, lista: Lista, offset: number): Promise<Page<Post>> {
  return apiGet<Page<Post>>(`${rota(username)}/${lista}?offset=${offset}&limit=${TAMANHO_PAGINA}`);
}

export function mudarVisibilidade(lista: Lista, visibilidade: Visibilidade): Promise<Biblioteca> {
  return apiPatch<Biblioteca>("/usuarios/eu/biblioteca", { [lista]: visibilidade });
}
