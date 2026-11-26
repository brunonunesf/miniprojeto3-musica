"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { AcaoDerivar } from "@/components/AcaoDerivar";
import { useSessao } from "@/components/AuthProvider";
import { BotaoCurtir } from "@/components/BotaoCurtir";
import { CamposReview } from "@/components/CamposReview";
import { Capa } from "@/components/Capa";
import { Comentarios } from "@/components/Comentarios";
import { MensagemErro } from "@/components/MensagemErro";
import { SeloDeOrigem } from "@/components/SeloDeOrigem";
import { apiDelete, apiGet, apiPatch, type Post } from "@/lib/api";
import { nomeDaVersao } from "@/lib/musica";

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  // A key recria o componente a cada review: nenhum estado passa de uma para outra.
  return <Review key={id} id={id} />;
}

function Review({ id }: { id: string }) {
  const { usuario } = useSessao();
  const [post, setPost] = useState<Post | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);
  const [editando, setEditando] = useState(false);

  useEffect(() => {
    let ativa = true;
    setErro("");
    apiGet<Post>(`/posts/${encodeURIComponent(id)}`).then(
      (resposta) => {
        if (ativa) setPost(resposta);
      },
      (falha: Error) => {
        if (ativa) setErro(falha.message);
      },
    );
    return () => {
      ativa = false;
    };
  }, [id, tentativa]);

  if (erro) {
    return (
      <div className="space-y-4">
        <MensagemErro>{erro}</MensagemErro>
        <button className="btn-primary" onClick={() => setTentativa((n) => n + 1)}>Tentar novamente</button>
      </div>
    );
  }
  if (!post) return <p role="status" className="text-zinc-600">Carregando review…</p>;

  const minha = usuario?.id === post.autor.id;

  return (
    <div className="space-y-6">
      <article className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <header className="flex flex-wrap items-center gap-5">
          <Capa musica={post.musica} />
          <div className="min-w-0 flex-1 space-y-1">
            <h1 className="break-words text-3xl font-bold tracking-tight">{post.musica.titulo}</h1>
            <p className="break-words text-lg text-zinc-700">{post.musica.artista}</p>
            <p className="break-words text-sm text-zinc-500">{nomeDaVersao(post.musica)}</p>
          </div>
          <p className="text-3xl font-bold text-brand-700">{post.nota}<span className="text-base text-zinc-500">/10</span></p>
        </header>
        {post.texto && <p className="whitespace-pre-wrap break-words leading-relaxed">{post.texto}</p>}
        <p className="text-sm text-zinc-500">
          Review de{" "}
          <Link href={`/usuarios/${post.autor.username}`} className="font-semibold text-brand-700">{post.autor.name}</Link>
          {" "}em {new Date(post.created_at).toLocaleDateString("pt-BR")}
        </p>
        <SeloDeOrigem post={post} />
        <div className="flex flex-wrap items-center gap-3">
          <BotaoCurtir post={post} />
          {!minha && <AcaoDerivar post={post} />}
        </div>
      </article>

      <Link href={`/posts/${post.id}/arvore`} className="inline-block font-semibold text-brand-700">
        Ver árvore de recomendações
      </Link>

      {minha && (editando ? (
        <EdicaoReview
          post={post}
          aoSalvar={(novo) => {
            setPost(novo);
            setEditando(false);
          }}
          aoCancelar={() => setEditando(false)}
        />
      ) : (
        <AcoesDoAutor postId={post.id} aoEditar={() => setEditando(true)} />
      ))}

      {post.comentarios !== undefined && <Comentarios postId={post.id} />}
    </div>
  );
}

type PropsEdicao = {
  post: Post;
  aoSalvar: (novo: Post) => void;
  aoCancelar: () => void;
};

function EdicaoReview({ post, aoSalvar, aoCancelar }: PropsEdicao) {
  const [nota, setNota] = useState(String(post.nota));
  const [texto, setTexto] = useState(post.texto);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    setSalvando(true);
    setErro("");
    try {
      aoSalvar(await apiPatch<Post>(`/posts/${post.id}`, { nota: Number(nota), texto }));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar.");
      setSalvando(false);
    }
  }

  return (
    <form onSubmit={salvar} aria-busy={salvando} className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold">Editar review</h2>
      <CamposReview nota={nota} texto={texto} aoMudarNota={setNota} aoMudarTexto={setTexto} />
      {erro && <MensagemErro>{erro}</MensagemErro>}
      <div className="flex flex-wrap items-center gap-4">
        <button type="submit" disabled={salvando} className="btn-primary">{salvando ? "Salvando…" : "Salvar"}</button>
        <button type="button" disabled={salvando} onClick={aoCancelar} className="text-sm font-semibold text-brand-700">Cancelar</button>
      </div>
    </form>
  );
}

function AcoesDoAutor({ postId, aoEditar }: { postId: number; aoEditar: () => void }) {
  const router = useRouter();
  const [confirmando, setConfirmando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState("");

  async function excluir() {
    setExcluindo(true);
    setErro("");
    try {
      await apiDelete(`/posts/${postId}`);
      router.replace("/");
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível excluir.");
      setExcluindo(false);
    }
  }

  return (
    <div className="space-y-4">
      {erro && <MensagemErro>{erro}</MensagemErro>}
      {confirmando ? (
        <div role="group" aria-label="Confirmar exclusão" className="space-y-3">
          <p>Excluir esta review? Não dá para desfazer.</p>
          <div className="flex flex-wrap items-center gap-4">
            <button className="btn-primary" disabled={excluindo} onClick={excluir}>{excluindo ? "Excluindo…" : "Confirmar exclusão"}</button>
            <button className="text-sm font-semibold text-brand-700" disabled={excluindo} onClick={() => setConfirmando(false)}>Cancelar</button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-4">
          <button className="btn-primary" onClick={aoEditar}>Editar review</button>
          <button className="text-sm font-semibold text-red-800" onClick={() => setConfirmando(true)}>Excluir</button>
        </div>
      )}
    </div>
  );
}
