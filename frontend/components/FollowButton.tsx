"use client";
import { useEffect, useState } from "react";
import { useSessao } from "@/components/AuthProvider";
import { apiDelete, apiGet, apiPost } from "@/lib/api";

export function FollowButton({ username }: { username: string }) {
  const { usuario } = useSessao();
  const [seguindo, setSeguindo] = useState<boolean | null>(null);
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [tentativa, setTentativa] = useState(0);
  useEffect(() => {
    let ativa = true; setSeguindo(null); setErro("");
    apiGet<{ seguindo: boolean }>(`/usuarios/${encodeURIComponent(username)}/follow`)
      .then(e => { if (ativa) setSeguindo(e.seguindo); }).catch(e => { if (ativa) setErro(e.message); });
    return () => { ativa = false; };
  }, [username, tentativa]);
  if (usuario?.username === username) return null;
  async function alternar() {
    setOcupado(true); setErro("");
    try {
      const path = `/usuarios/${encodeURIComponent(username)}/follow`;
      if (seguindo) await apiDelete(path); else await apiPost(path);
      setSeguindo(!seguindo);
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível atualizar."); }
    finally { setOcupado(false); }
  }
  return <div className="my-4">
    {erro && <p role="alert" className="mb-3">{erro}</p>}
    {seguindo === null ? erro ? <button onClick={() => setTentativa(t => t + 1)}>Tentar novamente</button> : <p role="status">Carregando vínculo…</p> : <button className="btn-primary" aria-pressed={seguindo} disabled={ocupado} onClick={() => void alternar()}>{ocupado ? "Salvando…" : seguindo ? "Deixar de seguir" : "Seguir"}</button>}
  </div>;
}
