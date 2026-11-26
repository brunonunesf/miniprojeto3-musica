import Link from "next/link";

import type { Post } from "@/lib/api";

/** De onde a review partiu; nada para uma review independente. */
export function SeloDeOrigem({ post }: { post: Post }) {
  if (!post.origem && !post.origem_id) return null;
  return (
    <p className="selo flex flex-wrap items-center gap-x-3">
      <span>{post.origem ? `A partir da review de ${post.origem.autor.name}` : "A partir de uma review apagada"}</span>
      <Link href={`/posts/${post.id}/arvore`} className="font-semibold text-brand-700 underline">Ver árvore</Link>
    </p>
  );
}
