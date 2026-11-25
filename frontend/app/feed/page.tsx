"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { ReviewCard } from "@/components/ReviewCard";
import type { Post } from "@/lib/api";
import { ARVORE_SIMULADA } from "@/lib/arvore";
import { buscarFeed, FEED_SIMULADO } from "@/lib/feed";

type Feed = { items: Post[]; proximo: number; temMais: boolean };

/** Junta duas páginas sem repetir reviews: novas publicações deslocam o offset. */
function juntar(atuais: Post[], novos: Post[]): Post[] {
  const vistos = new Set(atuais.map((post) => post.id));
  return [...atuais, ...novos.filter((post) => !vistos.has(post.id))];
}

export default function FeedPage() {
  const [feed, setFeed] = useState<Feed | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<{ mensagem: string; offset: number } | null>(null);
  // Só a resposta do pedido mais recente vale.
  const pedido = useRef(0);

  // offset 0 recomeça o feed; os demais acrescentam. Em falha, o que já apareceu fica.
  const carregar = useCallback(async (offset: number) => {
    const atual = ++pedido.current;
    setCarregando(true);
    setErro(null);
    try {
      const pagina = await buscarFeed(offset);
      if (atual !== pedido.current) return;
      const proximo = offset + pagina.items.length;
      setFeed((anterior) => ({
        items: juntar(offset === 0 || !anterior ? [] : anterior.items, pagina.items),
        proximo,
        temMais: pagina.items.length > 0 && proximo < pagina.total,
      }));
    } catch (falha) {
      if (atual !== pedido.current) return;
      setErro({ mensagem: falha instanceof Error ? falha.message : "Não foi possível carregar o feed.", offset });
    }
    setCarregando(false);
  }, []);

  useEffect(() => {
    void carregar(0);
    return () => {
      pedido.current++;
    };
  }, [carregar]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold tracking-tight">Feed</h1>
        <button className="text-sm font-semibold text-brand-700" disabled={carregando} onClick={() => void carregar(0)}>
          Atualizar
        </button>
      </div>

      {FEED_SIMULADO && (
        <p className="rounded-xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">
          Dados de exemplo: estas reviews são fictícias e não vêm do servidor.
        </p>
      )}

      {ARVORE_SIMULADA && (
        <Link href="/posts/3/arvore" className="inline-block font-semibold text-brand-700">
          Ver uma árvore de exemplo
        </Link>
      )}

      {feed?.items.map((post) => <ReviewCard key={post.id} post={post} exemplo={FEED_SIMULADO} />)}

      {feed && feed.items.length === 0 && !carregando && !erro && (
        <div className="space-y-3 rounded-2xl border border-zinc-200 bg-white p-6">
          <p>Nenhuma review por aqui ainda. O feed mostra as publicações de quem você segue.</p>
          <Link href="/usuarios" className="btn-primary">Conhecer pessoas</Link>
        </div>
      )}

      {carregando && <p role="status" className="text-center text-zinc-600">Carregando o feed…</p>}

      {erro && (
        <div className="space-y-3">
          <MensagemErro>{erro.mensagem}</MensagemErro>
          <button className="btn-primary" onClick={() => void carregar(erro.offset)}>Tentar novamente</button>
        </div>
      )}

      {feed?.temMais && !erro && (
        <button className="btn-primary w-full" disabled={carregando} onClick={() => void carregar(feed.proximo)}>
          Carregar mais
        </button>
      )}
    </div>
  );
}
