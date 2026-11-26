"use client";

import Link from "next/link";
import { useState } from "react";

import { nomeDaVersao } from "@/lib/musica";
import { LIMITE_DA_BUSCA, useBuscaDeMusicas } from "@/lib/useBuscaDeMusicas";

export function PesquisaDeMusicas() {
  const [busca, setBusca] = useState("");
  const [offset, setOffset] = useState(0);
  const termo = busca.trim();
  const { pagina, erro, repetir } = useBuscaDeMusicas(termo || null, offset);

  return (
    <div className="space-y-3">
      <input
        type="search"
        aria-label="Buscar música ou artista"
        placeholder="Buscar música ou artista"
        maxLength={200}
        value={busca}
        onChange={(e) => {
          setBusca(e.target.value);
          setOffset(0);
        }}
        className="field-input"
      />
      {erro && (
        <p className="text-sm text-red-800">
          {erro}{" "}
          <button type="button" className="font-semibold underline" onClick={repetir}>Repetir a busca</button>
        </p>
      )}
      {termo && !pagina && !erro && <p role="status" className="text-sm text-zinc-600">Buscando…</p>}
      {pagina && pagina.total === 0 && <p className="text-sm text-zinc-600">Nenhuma música encontrada.</p>}
      {pagina && pagina.items.length > 0 && (
        <ul className="divide-y divide-zinc-100">
          {pagina.items.map((musica) => (
            <li key={musica.id}>
              <Link href={`/musicas/${musica.id}`} className="block break-words py-2 hover:text-brand-700">
                <span className="block font-semibold">{musica.titulo}</span>
                <span className="block text-sm text-zinc-600">{musica.artista} · {nomeDaVersao(musica)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      {pagina && pagina.total > LIMITE_DA_BUSCA && (
        <div className="flex justify-between text-sm font-semibold text-brand-700">
          <button type="button" disabled={offset === 0} className="disabled:opacity-40" onClick={() => setOffset(offset - LIMITE_DA_BUSCA)}>Anteriores</button>
          <button type="button" disabled={offset + LIMITE_DA_BUSCA >= pagina.total} className="disabled:opacity-40" onClick={() => setOffset(offset + LIMITE_DA_BUSCA)}>Próximas</button>
        </div>
      )}
    </div>
  );
}
