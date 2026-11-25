"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { MusicSelector } from "@/components/MusicSelector";
import { ApiError, apiPost, type Music, type Post } from "@/lib/api";

export default function NovaReview() {
  const router = useRouter();
  const [musica, setMusica] = useState<Music | null>(null);
  const [texto, setTexto] = useState("");
  const [erro, setErro] = useState("");
  const [existente, setExistente] = useState<number | null>(null);
  const [salvando, setSalvando] = useState(false);
  async function publicar(e: React.FormEvent) {
    e.preventDefault();
    if (!musica || !texto.trim()) { setErro("Selecione uma música e escreva sua review."); return; }
    setSalvando(true); setErro(""); setExistente(null);
    try {
      const post = await apiPost<Post>("/posts", { texto, musica_id: musica.id });
      router.push(`/posts/${post.id}`);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível publicar.");
      if (e instanceof ApiError && e.postId) setExistente(e.postId);
    } finally { setSalvando(false); }
  }
  return <div className="space-y-5">
    <h1 className="text-3xl font-bold">Nova review</h1>
    {musica && <p role="status">Selecionada: <strong>{musica.titulo} — {musica.artista}</strong> · {musica.descricao_versao}</p>}
    <MusicSelector value={musica?.id ?? null} onChange={(_id, m) => { setMusica(m); setExistente(null); setErro(""); }} />
    <form onSubmit={publicar} className="space-y-4">
      <label className="block">Sua review<textarea required maxLength={3000} value={texto} disabled={salvando} onChange={e => setTexto(e.target.value)} className="mt-2 min-h-40 w-full rounded-lg border bg-white p-3" /></label>
      {erro && <p role="alert">{erro}</p>}
      {existente && <div className="flex flex-wrap gap-4"><Link className="font-bold text-brand-700" href={`/posts/${existente}`}>Abrir review existente</Link><Link className="font-bold text-brand-700" href={`/posts/${existente}?editar=1`}>Editar review existente</Link></div>}
      <button className="btn-primary disabled:opacity-50" disabled={salvando}>{salvando ? "Publicando…" : "Publicar review"}</button>
    </form>
  </div>;
}
