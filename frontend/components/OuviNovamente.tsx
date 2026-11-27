"use client";

import { useState, type FormEvent } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { COMENTARIO_MAXIMO, publicarReescuta, servidorAceitaReescuta } from "@/lib/reescuta";
import { useDisponivel } from "@/lib/useDisponivel";

/** Avisa que a pessoa ouviu de novo uma música que já avaliou. Não cria review nem pontua. */
export function OuviNovamente({ postId }: { postId: number }) {
  const disponivel = useDisponivel(servidorAceitaReescuta);
  const [aberto, setAberto] = useState(false);
  const [comentario, setComentario] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [falha, setFalha] = useState("");
  const [publicado, setPublicado] = useState(false);

  if (!disponivel) return null;

  async function publicar(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    setFalha("");
    try {
      await publicarReescuta(postId, comentario.trim());
      setComentario("");
      setAberto(false);
      setPublicado(true);
    } catch (erro) {
      // O comentário digitado continua no campo. No bloqueio de 24 horas, o servidor diz quanto falta.
      setFalha(erro instanceof Error ? erro.message : "Não foi possível publicar o aviso.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="space-y-3">
      {publicado && <p role="status" className="text-green-800">Aviso publicado para quem segue você.</p>}
      {aberto ? (
        <form onSubmit={publicar} aria-busy={enviando} className="painel space-y-3">
          <label htmlFor="reescuta" className="field-label">Comentário da reescuta (opcional)</label>
          <textarea id="reescuta" rows={3} maxLength={COMENTARIO_MAXIMO} value={comentario} onChange={(e) => setComentario(e.target.value)} className="field-input resize-y" />
          {falha && <MensagemErro>{falha}</MensagemErro>}
          <div className="flex flex-wrap items-center gap-4">
            <button type="submit" disabled={enviando} className="btn-primary">{enviando ? "Publicando…" : "Publicar aviso"}</button>
            <button type="button" disabled={enviando} className="text-sm font-semibold text-brand-700" onClick={() => { setAberto(false); setFalha(""); }}>
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <button type="button" className="btn-secundario" onClick={() => { setPublicado(false); setAberto(true); }}>
          Ouvi novamente
        </button>
      )}
    </div>
  );
}
