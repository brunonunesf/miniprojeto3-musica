"use client";

import Link from "next/link";
import { useState } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { useBuscaFederada, NOMES_FONTES, ESTADOS_FONTES, type EscolhaMusical } from "@/lib/catalogoExterno";
import { nomeDaVersao } from "@/lib/musica";

type Props = {
  escolhida: EscolhaMusical | null;
  aoEscolher: (musica: EscolhaMusical) => void;
};

export function SeletorDeMusica({ escolhida, aoEscolher }: Props) {
  const [busca, setBusca] = useState("");
  const { pagina, erro, repetir } = useBuscaFederada(busca);

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

      {pagina && Object.entries(pagina.fontes).map(([fonte, estado]) => ESTADOS_FONTES[estado] ? (
        <p key={fonte} className="text-sm text-zinc-600">{NOMES_FONTES[fonte]}: {ESTADOS_FONTES[estado]}. As outras fontes continuam disponíveis.</p>
      ) : null)}
      {erro && (
        <div className="space-y-2">
          <MensagemErro>{erro}</MensagemErro>
          <button type="button" className="text-sm font-semibold text-brand-700" onClick={repetir}>
            Buscar de novo
          </button>
        </div>
      )}
      {!pagina && !erro && <p role="status" className="text-sm text-zinc-600">Carregando o catálogo…</p>}
      {pagina && pagina.items.length === 0 && <p className="text-sm text-zinc-600">Nenhuma música encontrada no catálogo.</p>}

      {pagina && pagina.items.length === 0 && (
        <Link className="text-sm font-semibold underline" href={`/musicas/solicitacoes?titulo=${encodeURIComponent(busca.trim())}`}>Solicitar inclusão de uma música</Link>
      )}
      <p className="text-sm text-zinc-600"><Link className="underline" href="/musicas/solicitacoes">Meus pedidos de inclusão</Link></p>
      {pagina && pagina.items.length > 0 && (
        <ul className="max-h-72 space-y-2 overflow-y-auto">
          {pagina.items.map((musica) => (
            <li key={musica.chave}>
              <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-zinc-200 p-3 has-[:checked]:border-brand-500 has-[:checked]:bg-orange-50">
                <input
                  type="radio"
                  name="musica"
                  className="mt-1 accent-brand-600"
                  checked={escolhida?.chave === musica.chave}
                  onChange={() => aoEscolher(musica)}
                  onClick={() => {
                    // Permite renovar a seleção expirada clicando no mesmo resultado de uma nova busca.
                    if (escolhida?.chave === musica.chave) aoEscolher(musica);
                  }}
                />
                <span className="min-w-0 break-words">
                  <span className="block font-semibold">{musica.musica.titulo}</span>
                  <span className="block text-sm text-zinc-700">{musica.musica.artista}</span>
                  <span className="block text-sm text-zinc-500">{nomeDaVersao(musica.musica)}</span>
                  {musica.musica.album && <span className="block text-sm text-zinc-500">Álbum: {musica.musica.album}</span>}
                  <span className="block text-xs text-zinc-500">{musica.fontes.map((f) => NOMES_FONTES[f]).join(" · ")}</span>
                </span>
              </label>
              {musica.referencias.map((ref) => <a key={`${ref.servico}:${ref.url}`} href={ref.url} target="_blank" rel="noopener noreferrer" className="mr-3 text-sm underline">Abrir no {NOMES_FONTES[ref.servico]}</a>)}
            </li>
          ))}
        </ul>
      )}
      {pagina && (pagina.total_local > 20 || pagina.items.some((i) => i.selecao_externa)) && (
        <p className="text-sm text-zinc-600">Exibindo os primeiros resultados de cada fonte. Refine a busca se necessário.</p>
      )}

      {escolhida && (
        <p role="status" className="break-words text-sm">
          Selecionada: <strong>{escolhida.musica.titulo} — {escolhida.musica.artista}</strong> ({nomeDaVersao(escolhida.musica)})
        </p>
      )}
    </fieldset>
  );
}
