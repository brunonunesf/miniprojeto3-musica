"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { CamposReview } from "@/components/CamposReview";
import { MensagemErro } from "@/components/MensagemErro";
import { apiPost, type Post } from "@/lib/api";

const MUSICA_VAZIA = { titulo: "", artista: "", versao: "", capa_url: "" };

export default function NovaReviewPage() {
  const router = useRouter();
  const [musica, setMusica] = useState(MUSICA_VAZIA);
  const [nota, setNota] = useState("");
  const [texto, setTexto] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  function mudar(campo: keyof typeof MUSICA_VAZIA, valor: string) {
    setMusica((atual) => ({ ...atual, [campo]: valor }));
  }

  async function publicar(evento: FormEvent) {
    evento.preventDefault();
    if (!musica.titulo.trim() || !musica.artista.trim()) {
      setErro("Informe o título e o artista da música.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const post = await apiPost<Post>("/posts", {
        musica: {
          titulo: musica.titulo,
          artista: musica.artista,
          versao: musica.versao.trim() || "original",
          capa_url: musica.capa_url.trim(),
        },
        nota: Number(nota),
        texto,
      });
      router.push(`/posts/${post.id}`);
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível publicar.");
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Nova review</h1>
      <form onSubmit={publicar} aria-busy={salvando} className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div>
          <label htmlFor="titulo" className="field-label">Título da música</label>
          <input id="titulo" required maxLength={200} value={musica.titulo} onChange={(e) => mudar("titulo", e.target.value)} className="field-input" />
        </div>
        <div>
          <label htmlFor="artista" className="field-label">Artista</label>
          <input id="artista" required maxLength={200} value={musica.artista} onChange={(e) => mudar("artista", e.target.value)} className="field-input" />
        </div>
        <div>
          <label htmlFor="versao" className="field-label">Versão (opcional)</label>
          <input id="versao" maxLength={60} placeholder="original, remix, ao vivo…" value={musica.versao} onChange={(e) => mudar("versao", e.target.value)} className="field-input" />
        </div>
        <div>
          <label htmlFor="capa" className="field-label">Capa (endereço de uma imagem, opcional)</label>
          <input id="capa" type="url" maxLength={300} placeholder="https://exemplo.com/capa.png" value={musica.capa_url} onChange={(e) => mudar("capa_url", e.target.value)} className="field-input" />
        </div>
        <CamposReview nota={nota} texto={texto} aoMudarNota={setNota} aoMudarTexto={setTexto} />
        {erro && <MensagemErro>{erro}</MensagemErro>}
        <button type="submit" disabled={salvando} className="btn-primary w-full">
          {salvando ? "Publicando…" : "Publicar review"}
        </button>
      </form>
    </div>
  );
}
