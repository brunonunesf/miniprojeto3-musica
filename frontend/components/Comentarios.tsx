"use client";

import Link from "next/link";
import { useCallback, useState, type FormEvent } from "react";

import { useSessao } from "@/components/AuthProvider";
import { Avatar } from "@/components/Avatar";
import { MensagemErro } from "@/components/MensagemErro";
import { ApiError, apiDelete, apiGet, apiPost, type Comentario, type Page } from "@/lib/api";
import { tempoRelativo } from "@/lib/tempo";
import { usePaginacao } from "@/lib/usePaginacao";

const TAMANHO_PAGINA = 20;
const TAMANHO_MAXIMO = 1000;

export function Comentarios({ postId }: { postId: number }) {
  const rota = `/posts/${postId}/comentarios`;
  const buscar = useCallback(
    (offset: number) => apiGet<Page<Comentario>>(`${rota}?offset=${offset}&limit=${TAMANHO_PAGINA}`),
    [rota],
  );
  const { lista, carregando, erro, carregar, acrescentar, remover } = usePaginacao(buscar);
  const { usuario } = useSessao();
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [falha, setFalha] = useState("");
  const [aviso, setAviso] = useState("");

  async function comentar(evento: FormEvent) {
    evento.preventDefault();
    if (!texto.trim()) {
      setFalha("Escreva o comentário.");
      return;
    }
    setEnviando(true);
    setFalha("");
    setAviso("");
    try {
      const novo = await apiPost<Comentario>(rota, { texto });
      setTexto("");
      acrescentar(novo);
      if (lista?.temMais) setAviso("Comentário enviado. Ele aparece no fim da conversa.");
    } catch (erroDoEnvio) {
      // O texto digitado continua no campo.
      setFalha(erroDoEnvio instanceof Error ? erroDoEnvio.message : "Não foi possível comentar.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section id="comentarios" aria-labelledby="titulo-comentarios" className="painel space-y-4">
      <h2 id="titulo-comentarios" className="text-xl font-bold">Comentários</h2>

      {lista && lista.items.length > 0 && (
        <ul aria-label="Conversa" className="space-y-4">
          {lista.items.map((comentario) => (
            <li key={comentario.id} className="flex gap-3">
              <Avatar user={comentario.autor} />
              <div className="min-w-0 break-words">
                <p className="text-sm">
                  <Link href={`/usuarios/${comentario.autor.username}`} className="font-bold">{comentario.autor.name}</Link>
                  <span className="text-zinc-500"> · {tempoRelativo(comentario.created_at)}</span>
                </p>
                <p className="whitespace-pre-wrap">{comentario.texto}</p>
                {usuario?.id === comentario.autor.id && (
                  <ApagarComentario rota={`${rota}/${comentario.id}`} aoApagar={() => remover(comentario.id)} />
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      {lista && lista.items.length === 0 && !lista.temMais && !carregando && !erro && (
        <p className="text-zinc-600">Ninguém comentou ainda.</p>
      )}
      {carregando && <p role="status" className="text-sm text-zinc-600">Carregando comentários…</p>}
      {erro && (
        <div className="space-y-2">
          <MensagemErro>{erro.mensagem}</MensagemErro>
          <button type="button" className="btn-secundario" onClick={() => void carregar(erro.offset)}>Recarregar comentários</button>
        </div>
      )}
      {lista?.temMais && !erro && (
        <button type="button" className="btn-secundario w-full" disabled={carregando} onClick={() => void carregar(lista.proximo)}>
          Mais comentários
        </button>
      )}

      <form onSubmit={comentar} aria-busy={enviando} className="space-y-3">
        <label htmlFor="comentario" className="field-label">Seu comentário</label>
        <textarea id="comentario" rows={3} maxLength={TAMANHO_MAXIMO} value={texto} onChange={(e) => setTexto(e.target.value)} className="field-input resize-y" />
        {falha && <MensagemErro>{falha}</MensagemErro>}
        {aviso && <p role="status" className="text-sm text-zinc-600">{aviso}</p>}
        <button type="submit" disabled={enviando} className="btn-primary">{enviando ? "Enviando…" : "Comentar"}</button>
      </form>
    </section>
  );
}

function ApagarComentario({ rota, aoApagar }: { rota: string; aoApagar: () => void }) {
  const [confirmando, setConfirmando] = useState(false);
  const [apagando, setApagando] = useState(false);
  const [falha, setFalha] = useState("");

  async function apagar() {
    setApagando(true);
    setFalha("");
    try {
      await apiDelete(rota);
      aoApagar();
    } catch (erro) {
      const status = erro instanceof ApiError ? erro.status : 0;
      const mensagem = erro instanceof Error ? erro.message : "Não foi possível apagar.";
      // Um servidor sem a rota também responde 404 ou 405: nesses casos o comentário continua lá.
      if (status === 404 && mensagem === "comentário não encontrado") return aoApagar();
      setFalha(
        status === 405 || mensagem === "Not Found" ? "Este servidor ainda não permite apagar comentários." : mensagem,
      );
      setApagando(false);
    }
  }

  return (
    <div className="mt-1 space-y-2 text-sm">
      {falha && <MensagemErro>{falha}</MensagemErro>}
      {confirmando ? (
        <div role="group" aria-label="Confirmar exclusão do comentário" className="flex flex-wrap items-center gap-4">
          <span>Apagar este comentário? Não dá para desfazer.</span>
          <button type="button" className="font-semibold text-red-800" disabled={apagando} onClick={() => void apagar()}>
            {apagando ? "Apagando…" : "Confirmar"}
          </button>
          <button
            type="button"
            className="font-semibold text-brand-700"
            disabled={apagando}
            onClick={() => {
              setConfirmando(false);
              setFalha("");
            }}
          >
            Cancelar
          </button>
        </div>
      ) : (
        <button type="button" className="font-semibold text-red-800" onClick={() => setConfirmando(true)}>Apagar</button>
      )}
    </div>
  );
}
