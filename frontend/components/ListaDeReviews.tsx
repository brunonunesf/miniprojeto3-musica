import { Fragment, type ReactNode } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { ReviewCard } from "@/components/ReviewCard";
import type { Post } from "@/lib/api";
import type { usePaginacao } from "@/lib/usePaginacao";

type Props<T extends Post> = Pick<ReturnType<typeof usePaginacao<T>>, "lista" | "carregando" | "erro" | "carregar"> & {
  exemplo: boolean;
  /** Algo a mostrar acima de um cartão, como o motivo de uma sugestão. */
  antes?: (post: T) => ReactNode;
  /** O que mostrar quando não há nenhuma review. */
  vazio: ReactNode;
};

export function ListaDeReviews<T extends Post>({ lista, carregando, erro, carregar, exemplo, vazio, antes }: Props<T>) {
  return (
    <div className="space-y-5">
      {lista?.items.map((post) => (
        <Fragment key={post.id}>
          {antes?.(post)}
          <ReviewCard post={post} exemplo={exemplo} />
        </Fragment>
      ))}

      {lista && lista.items.length === 0 && !carregando && !erro && vazio}

      {carregando && <p role="status" className="text-center text-zinc-600">Carregando reviews…</p>}

      {erro && (
        <div className="space-y-3">
          <MensagemErro>{erro.mensagem}</MensagemErro>
          <button className="btn-primary" onClick={() => void carregar(erro.offset)}>Tentar novamente</button>
        </div>
      )}

      {lista?.temMais && !erro && (
        <button className="btn-secundario w-full" disabled={carregando} onClick={() => void carregar(lista.proximo)}>
          Carregar mais
        </button>
      )}
    </div>
  );
}
