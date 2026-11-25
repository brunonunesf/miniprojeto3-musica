"use client";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSessao } from "@/components/AuthProvider";
import { PostCard } from "@/components/PostCard";
import { ApiError, apiDelete, apiGet, apiPatch, type Post } from "@/lib/api";

export default function Detalhe({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { usuario } = useSessao();
  const router = useRouter();
  const [post, setPost] = useState<Post | null>(null);
  const [texto, setTexto] = useState("");
  const [editando, setEditando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [tentativa, setTentativa] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [ausente, setAusente] = useState(false);
  useEffect(() => {
    let ativa = true;
    setCarregando(true); setErro(""); setAusente(false);
    apiGet<Post>(`/posts/${id}`).then(p => {
      if (ativa) { setPost(p); setTexto(p.texto); setEditando(new URLSearchParams(window.location.search).has("editar")); }
    }).catch(e => { if (ativa) { setErro(e.message); setAusente(e instanceof ApiError && e.status === 404); } })
      .finally(() => { if (ativa) setCarregando(false); });
    return () => { ativa = false; };
  }, [id, tentativa]);
  async function salvar(e: React.FormEvent) {
    e.preventDefault(); if (!texto.trim()) { setErro("Escreva sua review."); return; }
    setOcupado(true); setErro("");
    try { const p = await apiPatch<Post>(`/posts/${id}`, { texto }); setPost(p); setTexto(p.texto); setEditando(false); setAviso("Alterações salvas."); }
    catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível salvar."); }
    finally { setOcupado(false); }
  }
  async function excluir() {
    setOcupado(true); setErro("");
    try { await apiDelete(`/posts/${id}`); router.push(`/pessoas/${usuario?.username}`); }
    catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível excluir."); }
    finally { setOcupado(false); }
  }
  if (carregando) return <p role="status">Carregando publicação…</p>;
  if (!post || ausente) return <div><h1 className="text-2xl font-bold">{ausente ? "Esta publicação não existe mais" : "Não foi possível carregar"}</h1><p role="alert" className="my-4">{erro}</p>{!ausente && <button className="btn-primary" onClick={() => setTentativa(t => t + 1)}>Tentar novamente</button>}</div>;
  const proprio = post.autor.id === usuario?.id;
  return <div className="space-y-5">
    <h1 className="text-3xl font-bold">{post.musica ? "Review" : "Publicação"}</h1>
    <PostCard post={post} />
    {aviso && <p role="status">{aviso}</p>}
    {erro && <p role="alert">{erro}</p>}
    {proprio && <>
      {editando ? <form onSubmit={salvar} className="space-y-3"><label className="block">Editar texto<textarea className="mt-2 min-h-40 w-full rounded-lg border bg-white p-3" required maxLength={3000} value={texto} disabled={ocupado} onChange={e => setTexto(e.target.value)} /></label><button className="btn-primary" disabled={ocupado}>Salvar alterações</button><button type="button" className="ml-4" disabled={ocupado} onClick={() => { setEditando(false); setTexto(post.texto); }}>Cancelar edição</button></form> : <button className="btn-primary" onClick={() => { setEditando(true); setAviso(""); }}>Editar texto</button>}
      <div>{confirmando ? <div role="group" aria-label="Confirmar exclusão"><p>Excluir esta publicação? O texto será apagado. Esta ação não pode ser desfeita.</p><button className="btn-primary mt-3" disabled={ocupado} onClick={() => void excluir()}>Confirmar exclusão</button><button className="ml-4" disabled={ocupado} onClick={() => setConfirmando(false)}>Cancelar</button></div> : <button className="text-red-800" disabled={ocupado} onClick={() => setConfirmando(true)}>Excluir publicação</button>}</div>
    </>}
    <Link className="inline-block font-bold text-brand-700" href="/posts/novo">Escrever outra review</Link>
  </div>;
}
