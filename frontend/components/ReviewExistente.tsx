"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { buscarReviewDaMusica } from "@/lib/reviewDaMusica";

type Props = { username: string; musicaId: number };

/** Acesso à review que a pessoa já tem da música; se não a achar, às reviews dela. */
export function ReviewExistente({ username, musicaId }: Props) {
  // undefined: procurando; null: não encontrada.
  const [reviewId, setReviewId] = useState<number | null | undefined>(undefined);

  useEffect(() => {
    let ativa = true;
    buscarReviewDaMusica(username, musicaId).then(
      (post) => {
        if (ativa) setReviewId(post?.id ?? null);
      },
      () => {
        if (ativa) setReviewId(null);
      },
    );
    return () => {
      ativa = false;
    };
  }, [username, musicaId]);

  if (reviewId === undefined) return <p role="status" className="text-sm text-zinc-600">Procurando a sua review…</p>;

  return (
    <Link
      href={reviewId === null ? `/usuarios/${username}` : `/posts/${reviewId}`}
      className="inline-block font-semibold text-brand-700"
    >
      {reviewId === null ? "Ver minhas reviews" : "Abrir a sua review desta música"}
    </Link>
  );
}
