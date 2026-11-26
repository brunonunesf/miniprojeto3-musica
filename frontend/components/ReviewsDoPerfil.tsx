"use client";

import { useCallback } from "react";

import { ListaDeReviews } from "@/components/ListaDeReviews";
import type { User } from "@/lib/api";
import { buscarReviewsDe, PERFIL_SIMULADO } from "@/lib/perfil";
import { usePaginacao } from "@/lib/usePaginacao";

export function ReviewsDoPerfil({ autor }: { autor: User }) {
  // O autor não muda enquanto o componente existe: a key do perfil o recria.
  const buscar = useCallback((offset: number) => buscarReviewsDe(autor, offset), [autor.username]);
  const reviews = usePaginacao(buscar);

  return (
    <section className="space-y-5" aria-labelledby="titulo-reviews">
      <h2 id="titulo-reviews" className="text-xl font-semibold">Reviews</h2>
      <ListaDeReviews {...reviews} exemplo={PERFIL_SIMULADO} vazio={<p className="text-zinc-600">Nenhuma review publicada ainda.</p>} />
    </section>
  );
}
