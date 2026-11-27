import { ApiError, apiDelete, apiGet, apiPost, type Page, type Post, type User } from "@/lib/api";
import { EXEMPLOS_DO_FEED } from "@/lib/feedExemplos";

/** Contadores e reputação são opcionais: um servidor mais antigo não os envia. */
export type Perfil = User & { seguidores?: number; seguindo?: number; eu_sigo?: boolean; reputacao?: number | null };

/** Avisa quem mostra reputação de que uma ação pode tê-la mudado. */
export const REPUTACAO_MUDOU = "reputacao-mudou";

// Ligado só em desenvolvimento, enquanto o backend não tem follow nem posts por usuário.
export const PERFIL_SIMULADO = process.env.NEXT_PUBLIC_PERFIL_SIMULADO === "true";
const TAMANHO_PAGINA = 10;
// No modo de exemplo, quem foi seguido vale até a página ser recarregada.
const seguidosDeExemplo = new Set<string>();

const rota = (username: string) => `/usuarios/${encodeURIComponent(username)}`;

export async function buscarPerfil(username: string): Promise<Perfil> {
  const perfil = await apiGet<Perfil>(rota(username));
  if (!PERFIL_SIMULADO) return perfil;
  const eu_sigo = seguidosDeExemplo.has(username);
  return { ...perfil, eu_sigo, seguidores: eu_sigo ? 4 : 3, seguindo: 5 };
}

export async function definirSeguir(username: string, seguir: boolean): Promise<void> {
  if (PERFIL_SIMULADO) {
    if (seguir) seguidosDeExemplo.add(username);
    else seguidosDeExemplo.delete(username);
    return;
  }
  const caminho = `${rota(username)}/follow`;
  await (seguir ? apiPost<void>(caminho) : apiDelete(caminho));
}

export async function buscarReviewsDe(autor: User, offset: number): Promise<Page<Post>> {
  if (PERFIL_SIMULADO) {
    const items = EXEMPLOS_DO_FEED.slice(offset, offset + TAMANHO_PAGINA).map((post) => ({ ...post, autor }));
    return { items, total: EXEMPLOS_DO_FEED.length, offset, limit: TAMANHO_PAGINA };
  }
  try {
    return await apiGet<Page<Post>>(`${rota(autor.username)}/posts?offset=${offset}&limit=${TAMANHO_PAGINA}`);
  } catch (falha) {
    if (falha instanceof ApiError && falha.status === 404) {
      throw new ApiError(404, "As reviews do perfil ainda não estão disponíveis neste servidor.");
    }
    throw falha;
  }
}
