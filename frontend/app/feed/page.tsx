"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet, type FeedItem, type Page } from "@/lib/api";
import { PostCard } from "@/components/PostCard";

export default function Feed() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [proximo, setProximo] = useState(0);
  const [tentativa, setTentativa] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  useEffect(() => {
    let ativa = true; setCarregando(true); setErro("");
    apiGet<Page<FeedItem>>(`/feed?offset=${offset}&limit=10`).then(p => {
      if (!ativa) return;
      setItems(anteriores => [...new Map([...(offset ? anteriores : []), ...p.items].map(item => [item.feed_id, item])).values()]);
      setTotal(p.total); setProximo(p.offset + p.items.length);
    }).catch(e => { if (ativa) setErro(e.message); })
      .finally(() => { if (ativa) setCarregando(false); });
    return () => { ativa = false; };
  }, [offset, tentativa]);
  return <div className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-3xl font-bold">Feed de quem você segue</h1><button className="btn-primary" disabled={carregando} onClick={() => { setOffset(0); setTentativa(t => t + 1); }}>Atualizar feed</button></div>
    {erro && <div role="alert"><p>{erro}</p><button className="btn-primary mt-3" onClick={() => setTentativa(t => t + 1)}>Tentar novamente</button></div>}
    {carregando && <p role="status">Carregando publicações…</p>}
    {!carregando && !erro && total === 0 && <p>Nenhuma publicação por aqui ainda. <Link className="text-brand-700 underline" href="/usuarios">Encontre pessoas para seguir.</Link></p>}
    {items.map(item => <section key={item.feed_id} aria-label={`${item.tipo === "republicacao" ? "Republicação" : "Publicação"} de ${item.autor.name}`}>
      {item.tipo === "republicacao" && <div className="mb-2 rounded-lg bg-orange-50 p-3"><p className="font-bold">Republicou · {new Date(item.feed_at).toLocaleString("pt-BR")}</p>{item.comentario && <p className="mt-2 whitespace-pre-wrap break-words">{item.comentario}</p>}</div>}
      <PostCard post={item} />
    </section>)}
    {!carregando && !erro && proximo < total && <button className="btn-primary" onClick={() => setOffset(proximo)}>Carregar mais</button>}
  </div>;
}
