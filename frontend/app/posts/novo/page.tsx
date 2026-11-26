"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, type FormEvent } from "react";

import { useSessao } from "@/components/AuthProvider";
import { CamposReview } from "@/components/CamposReview";
import { MensagemErro } from "@/components/MensagemErro";
import { SeletorDeMusica } from "@/components/SeletorDeMusica";
import { ApiError, apiGet, apiPost, type Musica, type Post } from "@/lib/api";
import { nomeDaVersao } from "@/lib/musica";

export default function NovaReviewPage() {
  // useSearchParams exige um limite de Suspense no build.
  return (
    <Suspense fallback={<p role="status" className="text-zinc-600">Carregando…</p>}>
      <NovaReview />
    </Suspense>
  );
}

function NovaReview() {
  const origemId = useSearchParams().get("origem");
  // A key recria o formulário quando a origem muda.
  return origemId ? <ReviewDerivada key={origemId} origemId={origemId} /> : <Formulario origem={null} />;
}

function ReviewDerivada({ origemId }: { origemId: string }) {
  const [origem, setOrigem] = useState<Post | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    let ativa = true;
    apiGet<Post>(`/posts/${encodeURIComponent(origemId)}`).then(
      (resposta) => {
        if (!ativa) return;
        if (resposta.origem_id === undefined) setErro("Este servidor ainda não aceita review derivada.");
        else setOrigem(resposta);
      },
      (falha: Error) => {
        if (ativa) setErro(falha.message);
      },
    );
    return () => {
      ativa = false;
    };
  }, [origemId]);

  if (erro) {
    return (
      <div className="space-y-4">
        <MensagemErro>{erro}</MensagemErro>
        <Link href="/feed" className="btn-secundario">Voltar ao feed</Link>
      </div>
    );
  }
  if (!origem) return <p role="status" className="text-zinc-600">Carregando a review de origem…</p>;
  return <Formulario origem={origem} />;
}

/** Sem origem, a pessoa escolhe a música; com origem, música e origem já vêm preenchidas. */
function Formulario({ origem }: { origem: Post | null }) {
  const router = useRouter();
  const { usuario } = useSessao();
  const [musica, setMusica] = useState<Musica | null>(origem?.musica ?? null);
  const [nota, setNota] = useState("");
  const [texto, setTexto] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [repetida, setRepetida] = useState(false);

  async function publicar(evento: FormEvent) {
    evento.preventDefault();
    if (!musica) {
      setErro("Escolha uma música do catálogo.");
      return;
    }
    if (origem && !texto.trim()) {
      setErro("A review derivada precisa da sua própria análise.");
      return;
    }
    setSalvando(true);
    setErro("");
    setRepetida(false);
    try {
      const dados = { musica_id: musica.id, nota: Number(nota), texto };
      const post = await apiPost<Post>("/posts", origem ? { ...dados, origem_id: origem.id } : dados);
      router.push(`/posts/${post.id}`);
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível publicar.");
      setRepetida(falha instanceof ApiError && falha.status === 409);
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">{origem ? "Nova review derivada" : "Nova review"}</h1>
      <form onSubmit={publicar} aria-busy={salvando} className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        {origem ? (
          <div className="selo space-y-1">
            <p>A partir da review de <strong>{origem.autor.name}</strong></p>
            <p className="break-words">
              <strong>{origem.musica.titulo} — {origem.musica.artista}</strong> ({nomeDaVersao(origem.musica)})
            </p>
          </div>
        ) : (
          <SeletorDeMusica
            escolhida={musica}
            aoEscolher={(nova) => {
              setMusica(nova);
              setErro("");
            }}
          />
        )}
        <CamposReview nota={nota} texto={texto} aoMudarNota={setNota} aoMudarTexto={setTexto} textoObrigatorio={origem !== null} />
        {erro && <MensagemErro>{erro}</MensagemErro>}
        {repetida && usuario && (
          <Link href={`/usuarios/${usuario.username}`} className="inline-block font-semibold text-brand-700">
            Ver minhas reviews
          </Link>
        )}
        <button type="submit" disabled={salvando} className="btn-primary w-full">
          {salvando ? "Publicando…" : "Publicar review"}
        </button>
      </form>
    </div>
  );
}
