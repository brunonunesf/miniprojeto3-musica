"use client";

import { useState } from "react";

import type { Musica } from "@/lib/api";

export function Capa({ musica, className = "size-28" }: { musica: Musica; className?: string }) {
  const [falhou, setFalhou] = useState(false);
  const classes = `${className} shrink-0 rounded-xl`;

  if (musica.capa_url && !falhou) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={musica.capa_url} alt={`Capa de ${musica.titulo}`} onError={() => setFalhou(true)} className={`${classes} object-cover`} />
    );
  }

  return (
    <div aria-hidden="true" className={`${classes} flex items-center justify-center bg-zinc-100 text-4xl text-brand-700`}>
      ♫
    </div>
  );
}
