"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, type FormEvent } from "react";
import { MensagemErro } from "@/components/MensagemErro";
import { apiGet, apiPost, type Page } from "@/lib/api";

type Pedido = { id: number; titulo: string; artista: string; versao: string; estado: string; motivo: string; musica_id: number | null };

export default function SolicitacoesPage() {
  return <Suspense fallback={<p role="status">Carregando pedidos…</p>}><Solicitacoes /></Suspense>;
}

function Solicitacoes() {
  const params = useSearchParams();
  const [titulo, setTitulo] = useState(params.get("titulo") ?? "");
  const [artista, setArtista] = useState("");
  const [versao, setVersao] = useState("");
  const [referencia, setReferencia] = useState("");
  const [justificativa, setJustificativa] = useState("");
  const [pagina, setPagina] = useState<Page<Pedido> | null>(null);
  const [offset, setOffset] = useState(0);
  const [tentativa, setTentativa] = useState(0);
  const [erroLista, setErroLista] = useState("");
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setPagina(null);
    setErroLista("");
    apiGet<Page<Pedido>>(`/musicas/solicitacoes?offset=${offset}&limit=20`, controller.signal).then(
      (p) => { if (!controller.signal.aborted) setPagina(p); },
      (e: Error) => { if (!controller.signal.aborted) setErroLista(e.message); },
    );
    return () => controller.abort();
  }, [offset, tentativa]);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setSalvando(true); setErro(""); setAviso("");
    try {
      await apiPost<Pedido>("/musicas/solicitacoes", { titulo, artista, versao, referencia, justificativa });
      setAviso("Pedido recebido. Após a aprovação, você poderá selecionar a música e publicar sua review.");
      setTitulo(""); setArtista(""); setVersao(""); setReferencia(""); setJustificativa("");
      setOffset(0); setTentativa((n) => n + 1);
    } catch (e) { setErro(e instanceof Error ? e.message : "Não foi possível enviar o pedido."); }
    finally { setSalvando(false); }
  }

  return <div className="space-y-6">
    <h1 className="text-3xl font-bold">Inclusão de músicas</h1>
    <p>Não encontrou uma música? Envie uma referência ou explique qual gravação deseja incluir. A review será publicada por você depois da aprovação.</p>
    <form onSubmit={enviar} aria-busy={salvando} className="space-y-4 rounded-2xl border bg-white p-6">
      <div><label className="field-label" htmlFor="pedido-titulo">Título</label><input id="pedido-titulo" required maxLength={200} className="field-input" value={titulo} onChange={(e) => setTitulo(e.target.value)} /></div>
      <div><label className="field-label" htmlFor="pedido-artista">Artista</label><input id="pedido-artista" required maxLength={200} className="field-input" value={artista} onChange={(e) => setArtista(e.target.value)} /></div>
      <div><label className="field-label" htmlFor="pedido-versao">Versão ou edição (opcional)</label><input id="pedido-versao" maxLength={200} className="field-input" value={versao} onChange={(e) => setVersao(e.target.value)} /></div>
      <div><label className="field-label" htmlFor="pedido-referencia">Link de referência</label><input id="pedido-referencia" type="url" maxLength={2048} className="field-input" value={referencia} onChange={(e) => setReferencia(e.target.value)} /></div>
      <div><label className="field-label" htmlFor="pedido-justificativa">Justificativa (obrigatória se não houver link)</label><textarea id="pedido-justificativa" required={!referencia.trim()} maxLength={1000} className="field-input" value={justificativa} onChange={(e) => setJustificativa(e.target.value)} /></div>
      {erro && <MensagemErro>{erro}</MensagemErro>}
      {aviso && <p role="status">{aviso}</p>}
      <button className="btn-primary" disabled={salvando}>{salvando ? "Enviando…" : "Solicitar inclusão"}</button>
    </form>
    <section className="space-y-3" aria-labelledby="meus-pedidos">
      <h2 id="meus-pedidos" className="text-xl font-bold">Meus pedidos</h2>
      <button type="button" className="text-sm underline" onClick={() => setTentativa((n) => n + 1)}>Atualizar pedidos</button>
      {erroLista && <MensagemErro>{erroLista}</MensagemErro>}
      {!pagina && !erroLista && <p role="status">Carregando pedidos…</p>}
      {pagina?.total === 0 && <p>Você ainda não tem pedidos.</p>}
      <ul className="space-y-3">{pagina?.items.map((p) => <li key={p.id} className="rounded-lg border bg-white p-4">
        <p className="break-words font-semibold">{p.titulo} — {p.artista}{p.versao ? ` · ${p.versao}` : ""}</p>
        <p>Estado: {p.estado}</p>{p.motivo && <p className="break-words">{p.motivo}</p>}
        {p.estado === "aprovado" && p.musica_id && <Link className="font-semibold underline" href={`/posts/novo?musica=${p.musica_id}`}>Escrever review</Link>}
      </li>)}</ul>
      {pagina && pagina.total > 20 && <div className="flex justify-between">
        <button disabled={offset === 0} onClick={() => setOffset((n) => n - 20)}>Anteriores</button>
        <button disabled={offset + 20 >= pagina.total} onClick={() => setOffset((n) => n + 20)}>Próximos</button>
      </div>}
    </section>
    <Link href="/posts/novo" className="underline">Voltar para nova review</Link>
  </div>;
}
