import Link from "next/link";
import type { Post } from "@/lib/api";

export function PostCard({ post }: { post: Post }) {
  return <article className="min-w-0 break-words rounded-xl border border-zinc-200 bg-white p-5">
    <Link href={`/pessoas/${post.autor.username}`} className="font-bold text-brand-700">{post.autor.name} · @{post.autor.username}</Link>
    {post.musica && <p className="mt-3 font-bold">{post.musica.titulo} — {post.musica.artista}<span className="block text-sm font-normal">{post.musica.tipo_versao.replaceAll("_", " ")} · {post.musica.descricao_versao}</span></p>}
    <p className="my-4 whitespace-pre-wrap break-words">{post.texto}</p>
    <p className="text-xs text-zinc-600">Publicada em <time dateTime={post.created_at}>{new Date(post.created_at).toLocaleString("pt-BR")}</time></p>
    {post.edited_at && <p className="mt-1 text-xs text-zinc-600">Editada em <time dateTime={post.edited_at}>{new Date(post.edited_at).toLocaleString("pt-BR")}</time></p>}
    <Link href={`/posts/${post.id}`} className="mt-4 inline-block text-sm font-bold text-brand-700">Abrir publicação</Link>
  </article>;
}
