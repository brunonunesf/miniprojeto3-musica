"use client";

import { useCallback } from "react";

import { ListaDeReviews } from "@/components/ListaDeReviews";
import type { User } from "@/lib/api";
import { buscarReviewsDe, PERFIL_SIMULADO } from "@/lib/perfil";
import { usePaginacao } from "@/lib/usePaginacao";

export function ReviewsDoPerfil({ autor }: { autor: User }) {
  // Nome e foto aparecem nos cartões: mudando um deles, a lista é buscada de novo.
  const buscar = useCallback(
    (offset: number) => buscarReviewsDe(autor, offset),
    [autor.username, autor.name, autor.avatar_url],
  );
  const reviews = usePaginacao(buscar);

  return (
    <section className="space-y-5" aria-labelledby="titulo-reviews">
      <h2 id="titulo-reviews" className="text-xl font-semibold">Reviews</h2>
      <ListaDeReviews {...reviews} exemplo={PERFIL_SIMULADO} vazio={<p className="text-zinc-600">Nenhuma review publicada ainda.</p>} />
    </section>
  );
}
