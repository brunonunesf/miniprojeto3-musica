import Link from "next/link";

import { Capa } from "@/components/Capa";
import type { Post } from "@/lib/api";

type Props = {
  post: Post;
  /** Reviews de exemplo não existem no servidor: sem links para elas. */
  exemplo?: boolean;
};

/** Cartão compacto: capa, música e nota. O texto completo fica no detalhe. */
export function ReviewCard({ post, exemplo = false }: Props) {
  const data = new Date(post.created_at).toLocaleDateString("pt-BR");
  return (
    <article className="space-y-4 rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
      <p className="break-words text-sm text-zinc-500">
        {exemplo ? (
          <span className="font-semibold">{post.autor.name}</span>
        ) : (
          <Link href={`/usuarios/${post.autor.username}`} className="font-semibold text-brand-700">{post.autor.name}</Link>
        )}
        {" "}· {data}
      </p>
      <div className="flex flex-wrap items-center gap-4">
        <Capa musica={post.musica} />
        <div className="min-w-0 flex-1 space-y-1">
          <h2 className="break-words text-xl font-bold">{post.musica.titulo}</h2>
          <p className="break-words text-zinc-700">{post.musica.artista}</p>
          <p className="break-words text-sm text-zinc-500">Versão: {post.musica.versao}</p>
        </div>
        <p className="text-2xl font-bold text-brand-700">{post.nota}<span className="text-sm text-zinc-500">/10</span></p>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <span className="text-zinc-500">{post.tem_texto ? "Tem análise" : "Só nota"}</span>
        {!exemplo && (
          <Link href={`/posts/${post.id}`} className="font-semibold text-brand-700">Abrir review</Link>
        )}
      </div>
    </article>
  );
}
