import Link from "next/link";

import type { Post } from "@/lib/api";

/**
 * Só vira link quando o servidor entende review derivada: um servidor antigo
 * ignoraria a origem e publicaria uma review sem ligação.
 */
export function AcaoDerivar({ post, exemplo = false }: { post: Post; exemplo?: boolean }) {
  const rotulo = (
    <>
      <span aria-hidden="true">→</span> Escrever review a partir desta
    </>
  );
  if (exemplo || post.origem_id === undefined) {
    return (
      <button type="button" disabled className="acao-card" title="Review derivada indisponível">
        {rotulo} <small>(em breve)</small>
      </button>
    );
  }
  return (
    <Link href={`/posts/novo?origem=${post.id}`} className="acao-card">
      {rotulo}
    </Link>
  );
}
