"use client";

import Link from "next/link";

import { ListaDeReviews } from "@/components/ListaDeReviews";
import { buscarFeed, FEED_SIMULADO } from "@/lib/feed";
import { usePaginacao } from "@/lib/usePaginacao";

export default function FeedPage() {
  const reviews = usePaginacao(buscarFeed);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold tracking-tight">Feed</h1>
        <button className="text-sm font-semibold text-brand-700" disabled={reviews.carregando} onClick={() => void reviews.carregar(0)}>
          Atualizar
        </button>
      </div>

      {FEED_SIMULADO && (
        <p className="rounded-xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">
          Dados de exemplo: estas reviews são fictícias e não vêm do servidor.
        </p>
      )}

      <ListaDeReviews
        {...reviews}
        exemplo={FEED_SIMULADO}
        vazio={
          <div className="space-y-3 rounded-2xl border border-zinc-200 bg-white p-6">
            <p>Nenhuma review por aqui ainda. O feed mostra as publicações de quem você segue.</p>
            <Link href="/usuarios" className="btn-primary">Conhecer pessoas</Link>
          </div>
        }
      />
    </div>
  );
}
