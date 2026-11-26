"use client";

import { useState } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { apiDelete, apiPost, type EstadoCurtida, type Post } from "@/lib/api";

export function BotaoCurtir({ post }: { post: Post }) {
  // A resposta vale só para a review recebida: ao recarregar, vale o que veio do servidor.
  const [resposta, setResposta] = useState<{ de: Post; estado: EstadoCurtida } | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  if (post.curtidas === undefined) return null;

  const estado =
    resposta?.de === post
      ? resposta.estado
      : { curtidas: post.curtidas, curtido_por_mim: post.curtido_por_mim === true };

  async function alternar() {
    setEnviando(true);
    setErro("");
    const rota = `/posts/${post.id}/curtir`;
    try {
      // O estado e a contagem vêm do servidor, nunca de uma conta feita aqui.
      const novo = await (estado.curtido_por_mim ? apiDelete<EstadoCurtida>(rota) : apiPost<EstadoCurtida>(rota));
      setResposta({ de: post, estado: novo });
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={enviando}
          aria-pressed={estado.curtido_por_mim}
          onClick={alternar}
          className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 text-sm font-semibold text-brand-700 aria-pressed:border-brand-500 aria-pressed:bg-orange-50 disabled:cursor-wait disabled:opacity-60"
        >
          <span aria-hidden="true">{estado.curtido_por_mim ? "♥" : "♡"}</span>
          {enviando ? "Enviando…" : estado.curtido_por_mim ? "Descurtir" : "Curtir"}
        </button>
        <span className="text-sm text-zinc-600">
          {estado.curtidas} {estado.curtidas === 1 ? "curtida" : "curtidas"}
        </span>
      </div>
      {erro && <MensagemErro>{erro}</MensagemErro>}
    </div>
  );
}
