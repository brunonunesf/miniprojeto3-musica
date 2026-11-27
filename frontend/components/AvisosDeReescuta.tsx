"use client";

import Link from "next/link";

import { MensagemErro } from "@/components/MensagemErro";
import { ReviewCard } from "@/components/ReviewCard";
import { buscarAvisos, servidorListaReescutas } from "@/lib/reescuta";
import { tempoRelativo } from "@/lib/tempo";
import { useDisponivel } from "@/lib/useDisponivel";
import { usePaginacao } from "@/lib/usePaginacao";

/** Avisos de reescuta de quem se segue, separados das reviews. Uma falha aqui não bloqueia o feed. */
export function AvisosDeReescuta() {
  return useDisponivel(servidorListaReescutas) ? <Avisos /> : null;
}

function Avisos() {
  const { lista, carregando, erro, carregar } = usePaginacao(buscarAvisos);
  if (!erro && !lista?.items.length) return null;

  return (
    <section aria-labelledby="titulo-reescutas" className="space-y-4">
      <h2 id="titulo-reescutas" className="text-xl font-bold">Ouvidas novamente</h2>
      {lista?.items.map((aviso) => (
        <div key={aviso.id} className="space-y-2">
          <p className="selo break-words">
            <strong>{aviso.review.autor.name}</strong> ouviu novamente · {tempoRelativo(aviso.created_at)}
          </p>
          {aviso.comentario && <p className="whitespace-pre-wrap break-words">{aviso.comentario}</p>}
          <Link href={`/posts/${aviso.review.id}`} className="inline-block text-sm font-semibold text-brand-700">
            Abrir a review atual
          </Link>
          <ReviewCard post={aviso.review} />
        </div>
      ))}
      {erro && (
        <div className="space-y-2">
          <MensagemErro>{erro.mensagem}</MensagemErro>
          <button type="button" className="btn-secundario" onClick={() => void carregar(erro.offset)}>Recarregar avisos</button>
        </div>
      )}
      {lista?.temMais && !erro && (
        <button type="button" className="btn-secundario w-full" disabled={carregando} onClick={() => void carregar(lista.proximo)}>
          Mais avisos
        </button>
      )}
    </section>
  );
}
