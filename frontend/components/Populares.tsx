"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Capa } from "@/components/Capa";
import type { Page } from "@/lib/api";
import { FEED_SIMULADO } from "@/lib/feed";
import { buscarPopulares, type MusicaPopular } from "@/lib/musicas";

export function Populares({ limite }: { limite: number }) {
  const [pagina, setPagina] = useState<Page<MusicaPopular> | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    let ativa = true;
    setErro("");
    buscarPopulares(0, limite).then(
      (resposta) => {
        if (ativa) setPagina(resposta);
      },
      (falha: Error) => {
        if (ativa) setErro(falha.message);
      },
    );
    return () => {
      ativa = false;
    };
  }, [limite, tentativa]);

  // Uma falha aqui não bloqueia o resto da página.
  if (erro) {
    return (
      <p className="text-sm text-zinc-600">
        {erro}{" "}
        <button type="button" className="font-semibold text-brand-700 underline" onClick={() => setTentativa((n) => n + 1)}>
          Recarregar músicas
        </button>
      </p>
    );
  }
  if (!pagina) return <p role="status" className="text-sm text-zinc-600">Carregando músicas…</p>;
  if (pagina.items.length === 0) return <p className="text-sm text-zinc-600">Nenhuma música avaliada ainda.</p>;

  return (
    <ul className="grid grid-cols-2 gap-3">
      {pagina.items.map((musica) => {
        const conteudo = (
          <>
            <Capa musica={musica} className="aspect-square w-full" />
            <span className="mt-2 block break-words font-bold">{musica.titulo}</span>
            <span className="block text-sm text-zinc-600">
              {musica.quantidade_reviews} {musica.quantidade_reviews === 1 ? "review" : "reviews"}
            </span>
          </>
        );
        return (
          <li key={musica.id} className="min-w-0">
            {FEED_SIMULADO ? conteudo : <Link href={`/musicas/${musica.id}`} className="block">{conteudo}</Link>}
          </li>
        );
      })}
    </ul>
  );
}
