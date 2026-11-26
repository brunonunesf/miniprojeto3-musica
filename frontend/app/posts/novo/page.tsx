"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { CamposReview } from "@/components/CamposReview";
import { MensagemErro } from "@/components/MensagemErro";
import { SeletorDeMusica } from "@/components/SeletorDeMusica";
import { apiPost, type Musica, type Post } from "@/lib/api";

export default function NovaReviewPage() {
  const router = useRouter();
  const [musica, setMusica] = useState<Musica | null>(null);
  const [nota, setNota] = useState("");
  const [texto, setTexto] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  async function publicar(evento: FormEvent) {
    evento.preventDefault();
    if (!musica) {
      setErro("Escolha uma música do catálogo.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const post = await apiPost<Post>("/posts", { musica_id: musica.id, nota: Number(nota), texto });
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
        <SeletorDeMusica
          escolhida={musica}
          aoEscolher={(nova) => {
            setMusica(nova);
            setErro("");
          }}
        />
        <CamposReview nota={nota} texto={texto} aoMudarNota={setNota} aoMudarTexto={setTexto} />
        {erro && <MensagemErro>{erro}</MensagemErro>}
        <button type="submit" disabled={salvando} className="btn-primary w-full">
          {salvando ? "Publicando…" : "Publicar review"}
        </button>
      </form>
    </div>
  );
}
