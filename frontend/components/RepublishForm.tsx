"use client";
import { useState } from "react";
import { apiPost } from "@/lib/api";

export function RepublishForm({ postId }: { postId: number }) {
  const [comentario, setComentario] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  async function republicar(e: React.FormEvent) {
    e.preventDefault(); setOcupado(true); setErro(""); setAviso("");
    try {
      await apiPost(`/posts/${postId}/republicacoes`, { comentario });
      setComentario(""); setAviso("Review republicada para seus seguidores.");
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível republicar."); }
    finally { setOcupado(false); }
  }
  return <section id="republicar" aria-label="Republicar review" className="rounded-xl border bg-white p-5">
    <h2 className="text-xl font-bold">Republicar review</h2>
    <p className="my-3 text-sm text-zinc-600">Traga sua review de volta ao feed de quem segue você. Uma republicação por música a cada 24 horas.</p>
    <form onSubmit={republicar} className="space-y-3">
      <label htmlFor="republicacao-comentario" className="block">Comentário opcional</label><textarea id="republicacao-comentario" className="mt-2 min-h-24 w-full rounded-lg border p-3" value={comentario} maxLength={280} disabled={ocupado} onChange={e => setComentario(e.target.value)} />
      {erro && <p role="alert">{erro}</p>}{aviso && <p role="status">{aviso}</p>}
      <button className="btn-primary" disabled={ocupado}>{ocupado ? "Republicando…" : "Republicar"}</button>
    </form>
  </section>;
}
