import type { Musica } from "@/lib/api";

const TIPOS: Record<Musica["tipo_versao"], string> = {
  original: "Original",
  desconhecida: "Versão não confirmada",
  remix: "Remix",
  ao_vivo: "Ao vivo",
  remaster: "Remaster",
};

/** Distingue gravações de mesmo título e artista. */
export function nomeDaVersao({ tipo_versao, descricao_versao }: Pick<Musica, "tipo_versao" | "descricao_versao">): string {
  return [TIPOS[tipo_versao], descricao_versao].filter(Boolean).join(" · ");
}
