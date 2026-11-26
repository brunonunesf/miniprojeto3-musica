"use client";

import { useEffect, useState } from "react";

import { apiGet, type Musica, type Page } from "@/lib/api";

export const LIMITE_DA_BUSCA = 20;
const ESPERA_DA_BUSCA_MS = 250;

/** Busca no catálogo. Com `busca` nula, não consulta o servidor. */
export function useBuscaDeMusicas(busca: string | null, offset = 0) {
  const [pagina, setPagina] = useState<Page<Musica> | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    if (busca === null) {
      setPagina(null);
      setErro("");
      return;
    }
    // Descarta a resposta de uma busca que já foi substituída.
    let ativa = true;
    const espera = setTimeout(() => {
      setErro("");
      apiGet<Page<Musica>>(`/musicas?q=${encodeURIComponent(busca)}&offset=${offset}&limit=${LIMITE_DA_BUSCA}`).then(
        (resposta) => {
          if (ativa) setPagina(resposta);
        },
        (falha: Error) => {
          if (!ativa) return;
          setPagina(null);
          setErro(falha.message);
        },
      );
    }, ESPERA_DA_BUSCA_MS);
    return () => {
      ativa = false;
      clearTimeout(espera);
    };
  }, [busca, offset, tentativa]);

  return { pagina, erro, repetir: () => setTentativa((n) => n + 1) };
}
