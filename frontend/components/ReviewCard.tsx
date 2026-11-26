import Link from "next/link";

import { Avatar } from "@/components/Avatar";
import { BotaoCurtir } from "@/components/BotaoCurtir";
import { Capa } from "@/components/Capa";
import { Compartilhar } from "@/components/Compartilhar";
import type { Post } from "@/lib/api";
import { nomeDaVersao } from "@/lib/musica";
import { tempoRelativo } from "@/lib/tempo";

type Props = {
  post: Post;
  /** Reviews de exemplo não existem no servidor: sem links nem ações para elas. */
  exemplo?: boolean;
};

/** Cartão compacto: capa, música e nota. O texto completo fica no detalhe. */
export function ReviewCard({ post, exemplo = false }: Props) {
  const detalhe = `/posts/${post.id}`;
  const analise = post.tem_texto ? "Tem análise" : "Só nota";
  return (
    <article className="space-y-3 rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
      <header className="flex items-center gap-3 text-sm">
        <Avatar user={post.autor} />
        <p className="min-w-0 break-words">
          {exemplo ? (
            <span className="font-bold">{post.autor.name}</span>
          ) : (
            <Link href={`/usuarios/${post.autor.username}`} className="font-bold">{post.autor.name}</Link>
          )}
          <span className="text-zinc-500"> · {tempoRelativo(post.created_at)}</span>
        </p>
      </header>

      <div className="flex flex-col gap-4 sm:flex-row">
        <Capa musica={post.musica} className="size-32 sm:size-44" />
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 break-words">
              <h2 className="text-xl font-bold">
                {exemplo ? post.musica.titulo : <Link href={detalhe} className="hover:text-brand-700">{post.musica.titulo}</Link>}
              </h2>
              <p className="text-zinc-700">{post.musica.artista}</p>
              <p className="text-sm italic text-zinc-500">{nomeDaVersao(post.musica)}</p>
            </div>
            <p className="text-4xl font-bold text-brand-700">{post.nota}<span className="text-2xl">/10</span></p>
          </div>

          {post.origem ? (
            <p className="selo flex flex-wrap items-center gap-x-3">
              <span>A partir da review de {post.origem.autor.name}</span>
              <Link href={`${detalhe}/arvore`} className="font-semibold text-brand-700 underline">Ver árvore</Link>
            </p>
          ) : (
            <p className="selo">{post.tem_texto && !exemplo ? <Link href={detalhe}>{analise}</Link> : analise}</p>
          )}

          <div className="mt-auto flex flex-wrap items-center gap-x-2 gap-y-1 border-t border-zinc-200 pt-2">
            <BotaoCurtir post={post} somenteLeitura={exemplo} />
            <button type="button" disabled className="acao-card" aria-label="Comentar (em breve)" title="Comentários em breve">
              <svg aria-hidden="true" viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M21 11.5a8.4 8.4 0 0 1-12.3 7.4L3 21l2.1-5.2A8.4 8.4 0 1 1 21 11.5Z" />
              </svg>
            </button>
            <button type="button" disabled className="acao-card" title="Review derivada em breve">
              <span aria-hidden="true">→</span> Escrever review a partir desta <small>(em breve)</small>
            </button>
            {!exemplo && <Compartilhar caminho={detalhe} titulo={`${post.musica.titulo} — ${post.musica.artista}`} />}
          </div>
        </div>
      </div>
    </article>
  );
}
