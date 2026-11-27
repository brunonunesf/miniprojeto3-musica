"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { ListaDeReviews } from "@/components/ListaDeReviews";
import { buscarSugestoes, DESCOBRIR_SIMULADO, descobrirIndisponivel } from "@/lib/descobrir";
import { usePaginacao } from "@/lib/usePaginacao";

export default function DescobrirPage() {
  const [indisponivel, setIndisponivel] = useState(false);
  const [personalizada, setPersonalizada] = useState(true);
  const buscar = useCallback(async (offset: number) => {
    try {
      const pagina = await buscarSugestoes(offset);
      setPersonalizada(pagina.personalizada);
      return pagina;
    } catch (falha) {
      if (!descobrirIndisponivel(falha)) throw falha;
      setIndisponivel(true);
      return { items: [], total: 0, offset, limit: 0 };
    }
  }, []);
  const sugestoes = usePaginacao(buscar);

  const pesquisar = <Link href="/musicas" className="btn-primary">Pesquisar músicas</Link>;

  if (indisponivel) {
    return (
      <section className="painel space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">Descobrir para você</h1>
        <p className="text-zinc-700">As sugestões a partir das suas reviews e curtidas ainda estão em preparação.</p>
        {pesquisar}
      </section>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Descobrir para você</h1>
          <p className="text-zinc-600">Reviews de músicas que você ainda não avaliou.</p>
        </div>
        <button type="button" className="btn-secundario" disabled={sugestoes.carregando} onClick={() => void sugestoes.carregar(0)}>
          Atualizar sugestões
        </button>
      </header>

      {DESCOBRIR_SIMULADO && (
        <p className="selo">Dados de exemplo: estas sugestões não vêm do servidor.</p>
      )}
      {!personalizada && (
        <p className="selo">
          Estas são reviews recentes e variadas. A personalização começa quando você avalia ou curte músicas.
        </p>
      )}

      <ListaDeReviews
        {...sugestoes}
        exemplo={DESCOBRIR_SIMULADO}
        antes={(sugestao) => <p className="text-sm font-semibold text-brand-700">{sugestao.explicacao}</p>}
        vazio={
          <div className="painel space-y-4">
            <p className="text-zinc-700">Nenhuma sugestão por enquanto.</p>
            {pesquisar}
          </div>
        }
      />
    </div>
  );
}
