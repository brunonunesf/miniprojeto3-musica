"use client";

import Link from "next/link";
import { useCallback, useState, type FormEvent } from "react";

import { Avatar } from "@/components/Avatar";
import { MensagemErro } from "@/components/MensagemErro";
import { apiGet, apiPost, type Comentario, type Page } from "@/lib/api";
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
  const { lista, carregando, erro, carregar, acrescentar } = usePaginacao(buscar);
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
              </div>
            </li>
          ))}
        </ul>
      )}
      {lista && lista.items.length === 0 && !carregando && !erro && (
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
