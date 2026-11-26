import type { ReactNode } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { ReviewCard } from "@/components/ReviewCard";
import type { usePaginacao } from "@/lib/usePaginacao";

type Props = ReturnType<typeof usePaginacao> & {
  exemplo: boolean;
  /** O que mostrar quando não há nenhuma review. */
  vazio: ReactNode;
};

export function ListaDeReviews({ lista, carregando, erro, carregar, exemplo, vazio }: Props) {
  return (
    <div className="space-y-5">
      {lista?.items.map((post) => <ReviewCard key={post.id} post={post} exemplo={exemplo} />)}

      {lista && lista.items.length === 0 && !carregando && !erro && vazio}

      {carregando && <p role="status" className="text-center text-zinc-600">Carregando reviews…</p>}

      {erro && (
        <div className="space-y-3">
          <MensagemErro>{erro.mensagem}</MensagemErro>
          <button className="btn-primary" onClick={() => void carregar(erro.offset)}>Tentar novamente</button>
        </div>
      )}

      {lista?.temMais && !erro && (
        <button className="btn-primary w-full" disabled={carregando} onClick={() => void carregar(lista.proximo)}>
          Carregar mais
        </button>
      )}
    </div>
  );
}
