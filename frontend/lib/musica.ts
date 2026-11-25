import type { Musica } from "@/lib/api";

const TIPOS: Record<Musica["tipo_versao"], string> = {
  original: "Original",
  remix: "Remix",
  ao_vivo: "Ao vivo",
  remaster: "Remaster",
};

/** Distingue gravações de mesmo título e artista. */
export function nomeDaVersao({ tipo_versao, descricao_versao }: Musica): string {
  return [TIPOS[tipo_versao], descricao_versao].filter(Boolean).join(" · ");
}
