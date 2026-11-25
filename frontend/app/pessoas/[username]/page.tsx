"use client";
import { use, useEffect, useState } from "react";
import { apiGet, type Page, type Post } from "@/lib/api";
import { FollowButton } from "@/components/FollowButton";
import { PostCard } from "@/components/PostCard";

export default function Publicacoes({ params }: { params: Promise<{ username: string }> }) {
  const { username } = use(params);
  const [pagina, setPagina] = useState<Page<Post> | null>(null);
  const [erro, setErro] = useState("");
  const [offset, setOffset] = useState(0);
  const [tentativa, setTentativa] = useState(0);
  const [carregando, setCarregando] = useState(true);
  useEffect(() => {
    let ativa = true; setCarregando(true); setErro("");
    apiGet<Page<Post>>(`/usuarios/${encodeURIComponent(username)}/posts?offset=${offset}&limit=10`)
      .then(p => { if (ativa) setPagina(p); }).catch(e => { if (ativa) setErro(e.message); })
      .finally(() => { if (ativa) setCarregando(false); });
    return () => { ativa = false; };
  }, [username, offset, tentativa]);
  return <div className="space-y-5"><h1 className="break-words text-3xl font-bold">Publicações de @{username}</h1><FollowButton username={username} />
    {carregando ? <p role="status">Carregando publicações…</p> : erro ? <div role="alert">{erro}<button className="btn-primary ml-3" onClick={() => setTentativa(t => t + 1)}>Tentar novamente</button></div> : pagina && <>
      {pagina.total === 0 && <p>Nenhuma publicação ainda.</p>}
      {pagina.items.map(p => <PostCard key={p.id} post={p} />)}
      {pagina.total > 10 && <div className="flex gap-4"><button disabled={!offset} onClick={() => setOffset(n => Math.max(0, n - 10))}>Anterior</button><button disabled={offset + 10 >= pagina.total} onClick={() => setOffset(n => n + 10)}>Próxima</button></div>}
    </>}
  </div>;
}
