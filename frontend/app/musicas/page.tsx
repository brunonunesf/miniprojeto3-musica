"use client";
import { useState } from "react";
import { MusicSelector } from "@/components/MusicSelector";
import type { Music } from "@/lib/api";

export default function Musicas() {
  const [selecionada, setSelecionada] = useState<Music | null>(null);
  return <>
    <h1 className="text-3xl font-bold">Catálogo musical</h1>
    <p className="mt-3 text-zinc-600">Encontre uma música e confira sua versão. O catálogo inicial usa artistas e faixas fictícios de demonstração.</p>
    {selecionada && <p role="status" className="mt-5 rounded-xl border border-orange-200 bg-orange-50 p-4">Música selecionada: <strong>{selecionada.titulo} — {selecionada.artista}</strong> · {selecionada.descricao_versao}</p>}
    <MusicSelector value={selecionada?.id ?? null} onChange={(_id, musica) => setSelecionada(musica)} />
    <p className="mt-6 text-sm text-zinc-600">Para publicar sua opinião, acesse “Escrever review” na navegação.</p>
  </>;
}
