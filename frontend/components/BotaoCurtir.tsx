"use client";

import { useState } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { apiDelete, apiPost, type EstadoCurtida, type Post } from "@/lib/api";
import { REPUTACAO_MUDOU } from "@/lib/perfil";

type Props = { post: Post; somenteLeitura?: boolean };

export function BotaoCurtir({ post, somenteLeitura = false }: Props) {
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
      window.dispatchEvent(new Event(REPUTACAO_MUDOU));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir.");
    } finally {
      setEnviando(false);
    }
  }

  const contagem = `${estado.curtidas} ${estado.curtidas === 1 ? "curtida" : "curtidas"}`;

  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <button
        type="button"
        disabled={enviando || somenteLeitura}
        aria-pressed={estado.curtido_por_mim}
        aria-label={enviando ? "Enviando…" : estado.curtido_por_mim ? "Descurtir" : "Curtir"}
        onClick={alternar}
        className="acao-card aria-pressed:text-brand-700"
      >
        <span aria-hidden="true" className="text-xl leading-none">{estado.curtido_por_mim ? "♥" : "♡"}</span>
        <span aria-hidden="true">{enviando ? "…" : estado.curtidas}</span>
      </button>
      <span className="sr-only">{contagem}</span>
      {erro && <MensagemErro>{erro}</MensagemErro>}
    </span>
  );
}
