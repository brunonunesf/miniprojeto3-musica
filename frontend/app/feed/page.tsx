"use client";

import Link from "next/link";

import { ListaDeReviews } from "@/components/ListaDeReviews";
import { PerfilLateral } from "@/components/PerfilLateral";
import { PesquisaDeMusicas } from "@/components/PesquisaDeMusicas";
import { Populares } from "@/components/Populares";
import { ARVORE_SIMULADA } from "@/lib/arvore";
import { buscarFeed, FEED_SIMULADO } from "@/lib/feed";
import { usePaginacao } from "@/lib/usePaginacao";

export default function FeedPage() {
  const reviews = usePaginacao(buscarFeed);

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[250px_minmax(0,1fr)_320px]">
      <aside aria-label="Seu perfil e atalhos" className="painel hidden lg:block">
        <PerfilLateral />
      </aside>

      <section aria-labelledby="titulo-feed" className="painel min-w-0 space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 id="titulo-feed" className="text-3xl font-bold tracking-tight">Seu feed</h1>
            <p className="text-zinc-600">Reviews de quem você segue</p>
          </div>
          <button className="btn-secundario" disabled={reviews.carregando} onClick={() => void reviews.carregar(0)}>
            <span aria-hidden="true">↻</span> Atualizar
          </button>
        </div>

        {/* Abaixo de 1024 px as colunas laterais viram estes atalhos. */}
        <div className="flex flex-wrap gap-3 lg:hidden">
          <Link href="/posts/novo" className="btn-primary">+ Escrever review</Link>
          <Link href="/musicas" className="btn-secundario">Pesquisar músicas</Link>
        </div>

        {FEED_SIMULADO && (
          <p className="rounded-xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">
            Dados de exemplo: reviews, contagens e músicas desta página são fictícias e não vêm do servidor.
          </p>
        )}

        {ARVORE_SIMULADA && (
          <Link href="/posts/3/arvore" className="inline-block font-semibold text-brand-700">
            Ver uma árvore de exemplo
          </Link>
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
      </section>

      <aside aria-label="Pesquisa e descoberta" className="hidden space-y-4 lg:block">
        <div className="painel">
          <PesquisaDeMusicas />
        </div>
        <section className="painel" aria-labelledby="titulo-populares">
          <h2 id="titulo-populares" className="text-xl font-bold">Mais avaliadas na comunidade</h2>
          <Populares limite={4} />
          <Link href="/musicas" className="mt-4 block text-center text-sm font-semibold text-brand-700 underline">Ver todas</Link>
        </section>
        <section className="rounded-2xl border border-orange-200 bg-orange-50 p-5" aria-labelledby="titulo-descobrir">
          <h2 id="titulo-descobrir" className="text-xl font-bold">Descobrir para você</h2>
          <p className="mt-2 text-sm text-zinc-700">Sugestões a partir das suas reviews e curtidas.</p>
          <Link href="/descobrir" className="mt-3 inline-block text-sm font-semibold text-brand-700">Explorar sugestões →</Link>
        </section>
      </aside>
    </div>
  );
}
