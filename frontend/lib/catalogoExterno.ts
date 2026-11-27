"use client";

import { useEffect, useState } from "react";
import { apiGet, type Musica } from "@/lib/api";

export type EscolhaMusical = {
  chave: string;
  musica_id: number | null;
  selecao_externa: string | null;
  musica: Pick<Musica, "titulo" | "artista" | "tipo_versao" | "descricao_versao" | "capa_url" | "generos" | "tags"> & { album?: string; duracao_ms?: number | null };
  fontes: string[];
  referencias: { servico: string; url: string }[];
};
export type BuscaFederada = { items: EscolhaMusical[]; total_local: number; fontes: Record<string, string> };

export function escolhaLocal(musica: Musica): EscolhaMusical {
  return { chave: `local:${musica.id}`, musica_id: musica.id, selecao_externa: null, musica, fontes: ["local"], referencias: [] };
}

export const NOMES_FONTES: Record<string, string> = { local: "Catálogo", spotify: "Spotify", deezer: "Deezer" };
export const ESTADOS_FONTES: Record<string, string> = {
  nao_habilitado: "a busca ainda não foi habilitada", sem_acesso: "sem acesso autorizado",
  indisponivel: "temporariamente indisponível", limite: "limite de consultas atingido",
  sem_assinatura: "seleção temporariamente indisponível",
};

export function useBuscaFederada(busca: string) {
  const [resposta, setResposta] = useState<{ consulta: string; tentativa: number; pagina?: BuscaFederada; erro?: string } | null>(null);
  const [tentativa, setTentativa] = useState(0);
  const consulta = busca.trim();
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiGet<BuscaFederada>(`/musicas/busca?q=${encodeURIComponent(consulta)}`, controller.signal).then(
        (pagina) => { if (!controller.signal.aborted) setResposta({ consulta, tentativa, pagina }); },
        (falha: Error) => { if (!controller.signal.aborted) setResposta({ consulta, tentativa, erro: falha.message }); },
      );
    }, 300);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [consulta, tentativa]);
  const atual = resposta?.consulta === consulta && resposta.tentativa === tentativa ? resposta : null;
  return { pagina: atual?.pagina, erro: atual?.erro, repetir: () => setTentativa((n) => n + 1) };
}
