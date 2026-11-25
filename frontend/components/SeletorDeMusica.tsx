"use client";

import { useEffect, useState } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { apiGet, type Musica, type Page } from "@/lib/api";
import { nomeDaVersao } from "@/lib/musica";

const LIMITE = 20;
const ESPERA_DA_BUSCA_MS = 250;

type Props = {
  escolhida: Musica | null;
  aoEscolher: (musica: Musica) => void;
};

export function SeletorDeMusica({ escolhida, aoEscolher }: Props) {
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState<Page<Musica> | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    // Descarta a resposta de uma busca que já foi substituída.
    let ativa = true;
    const espera = setTimeout(() => {
      setErro("");
      apiGet<Page<Musica>>(`/musicas?q=${encodeURIComponent(busca)}&limit=${LIMITE}`).then(
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
  }, [busca, tentativa]);

  return (
    <fieldset className="space-y-3">
      <legend className="field-label">Música</legend>
      <label htmlFor="busca-musica" className="sr-only">Buscar música por título ou artista</label>
      <input
        id="busca-musica"
        type="search"
        maxLength={200}
        placeholder="Busque por título ou artista"
        value={busca}
        onChange={(e) => setBusca(e.target.value)}
        // Enter na busca não deve publicar a review.
        onKeyDown={(e) => {
          if (e.key === "Enter") e.preventDefault();
        }}
        className="field-input"
      />

      {erro && (
        <div className="space-y-2">
          <MensagemErro>{erro}</MensagemErro>
          <button type="button" className="text-sm font-semibold text-brand-700" onClick={() => setTentativa((n) => n + 1)}>
            Buscar de novo
          </button>
        </div>
      )}
      {!pagina && !erro && <p role="status" className="text-sm text-zinc-600">Carregando o catálogo…</p>}
      {pagina && pagina.total === 0 && <p className="text-sm text-zinc-600">Nenhuma música encontrada no catálogo.</p>}

      {pagina && pagina.items.length > 0 && (
        <ul className="max-h-72 space-y-2 overflow-y-auto">
          {pagina.items.map((musica) => (
            <li key={musica.id}>
              <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-zinc-200 p-3 has-[:checked]:border-brand-500 has-[:checked]:bg-orange-50">
                <input
                  type="radio"
                  name="musica"
                  className="mt-1 accent-brand-600"
                  checked={escolhida?.id === musica.id}
                  onChange={() => aoEscolher(musica)}
                />
                <span className="min-w-0 break-words">
                  <span className="block font-semibold">{musica.titulo}</span>
                  <span className="block text-sm text-zinc-700">{musica.artista}</span>
                  <span className="block text-sm text-zinc-500">{nomeDaVersao(musica)}</span>
                </span>
              </label>
            </li>
          ))}
        </ul>
      )}
      {pagina && pagina.total > pagina.items.length && (
        <p className="text-sm text-zinc-600">Há mais resultados. Refine a busca.</p>
      )}

      {escolhida && (
        <p role="status" className="break-words text-sm">
          Selecionada: <strong>{escolhida.titulo} — {escolhida.artista}</strong> ({nomeDaVersao(escolhida)})
        </p>
      )}
    </fieldset>
  );
}
