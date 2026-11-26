"use client";

import { useState } from "react";

/** Usa o compartilhamento do aparelho; sem ele, copia o link da review. */
export function Compartilhar({ caminho, titulo }: { caminho: string; titulo: string }) {
  const [aviso, setAviso] = useState("");

  async function compartilhar() {
    const url = new URL(caminho, window.location.origin).toString();
    setAviso("");
    try {
      if (navigator.share) {
        await navigator.share({ title: titulo, url });
        return;
      }
      await navigator.clipboard.writeText(url);
      setAviso("Link copiado.");
    } catch (falha) {
      // Fechar a janela de compartilhamento não é erro.
      if (falha instanceof DOMException && falha.name === "AbortError") return;
      setAviso(`Não foi possível compartilhar. Link: ${url}`);
    }
  }

  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <button type="button" className="acao-card" aria-label="Compartilhar review" onClick={compartilhar}>
        <svg aria-hidden="true" viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M12 15V4m0 0L8 8m4-4 4 4M5 12v7h14v-7" />
        </svg>
      </button>
      {aviso && <span role="status" className="break-all text-xs text-zinc-600">{aviso}</span>}
    </span>
  );
}
