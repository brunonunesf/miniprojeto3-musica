"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Capa } from "@/components/Capa";
import { ListaDeReviews } from "@/components/ListaDeReviews";
import { MensagemErro } from "@/components/MensagemErro";
import { apiGet, type Musica } from "@/lib/api";
import { nomeDaVersao } from "@/lib/musica";
import { buscarReviewsDaMusica } from "@/lib/musicas";
import { usePaginacao } from "@/lib/usePaginacao";

export default function MusicaPage() {
  const { id } = useParams<{ id: string }>();
  return <MusicaDe key={id} id={id} />;
}

function MusicaDe({ id }: { id: string }) {
  const [musica, setMusica] = useState<Musica | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    let ativa = true;
    apiGet<Musica>(`/musicas/${encodeURIComponent(id)}`).then(
      (resposta) => {
        if (ativa) setMusica(resposta);
      },
      (falha: Error) => {
        if (ativa) setErro(falha.message);
      },
    );
    return () => {
      ativa = false;
    };
  }, [id]);

  if (erro) return <MensagemErro>{erro}</MensagemErro>;
  if (!musica) return <p role="status" className="text-zinc-600">Carregando música…</p>;

  return (
    <div className="space-y-6">
      <header className="painel flex flex-wrap items-center gap-5">
        <Capa musica={musica} />
        <div className="min-w-0 flex-1 break-words">
          <h1 className="text-3xl font-bold tracking-tight">{musica.titulo}</h1>
          <p className="text-lg text-zinc-700">{musica.artista}</p>
          <p className="text-sm italic text-zinc-500">{nomeDaVersao(musica)}</p>
        </div>
      </header>
      <ReviewsDaMusica id={id} />
    </div>
  );
}

function ReviewsDaMusica({ id }: { id: string }) {
  const buscar = useCallback((offset: number) => buscarReviewsDaMusica(id, offset), [id]);
  const reviews = usePaginacao(buscar);

  return (
    <section className="space-y-4" aria-labelledby="titulo-reviews">
      <h2 id="titulo-reviews" className="text-xl font-bold">Reviews</h2>
      <ListaDeReviews {...reviews} exemplo={false} vazio={<p className="text-zinc-600">Nenhuma review desta música ainda.</p>} />
    </section>
  );
}
