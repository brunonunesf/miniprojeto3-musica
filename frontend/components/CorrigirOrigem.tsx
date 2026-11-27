"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { apiGet, type Page, type Post } from "@/lib/api";
import { servidorCorrigeOrigem, trocarOrigem, type OrigemCorrigida } from "@/lib/origem";
import { usePaginacao } from "@/lib/usePaginacao";

type Props = { post: Post; aoCorrigir: (novo: OrigemCorrigida) => void };

/** Troca a origem de uma review derivada. Não transforma raiz em derivada nem remove a origem. */
export function CorrigirOrigem({ post, aoCorrigir }: Props) {
  const [disponivel, setDisponivel] = useState(false);
  const [aberto, setAberto] = useState(false);
  const [corrigida, setCorrigida] = useState(false);
  const [reputacaoPendente, setReputacaoPendente] = useState(false);

  useEffect(() => {
    let ativa = true;
    void servidorCorrigeOrigem().then((sim) => {
      if (ativa) setDisponivel(sim);
    });
    return () => {
      ativa = false;
    };
  }, []);

  if (!disponivel || !post.origem_id) return null;

  return (
    <section aria-labelledby="titulo-origem" className="painel space-y-4">
      <h2 id="titulo-origem" className="text-xl font-bold">Origem da review</h2>
      <p>{post.origem ? `Hoje: a review de ${post.origem.autor.name}.` : "Hoje: uma review apagada."}</p>
      {corrigida && <p role="status" className="text-green-800">Origem corrigida.{reputacaoPendente ? " Reputação temporariamente indisponível." : ""}</p>}
      {aberto ? (
        <EscolhaDeOrigem
          post={post}
          aoCancelar={() => setAberto(false)}
          aoCorrigir={(novo) => {
            setAberto(false);
            setCorrigida(true);
            setReputacaoPendente(novo.reputacao_disponivel === false);
            aoCorrigir(novo);
          }}
        />
      ) : (
        <button type="button" className="btn-secundario" onClick={() => { setCorrigida(false); setAberto(true); }}>
          Corrigir origem
        </button>
      )}
    </section>
  );
}

function EscolhaDeOrigem({ post, aoCorrigir, aoCancelar }: Props & { aoCancelar: () => void }) {
  const buscar = useCallback(
    (offset: number) => apiGet<Page<Post>>(`/musicas/${post.musica.id}/reviews?offset=${offset}&limit=20`),
    [post.musica.id],
  );
  const { lista, carregando, erro, carregar } = usePaginacao(buscar);
  const [escolhida, setEscolhida] = useState<Post | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [falha, setFalha] = useState("");
  // Ficam de fora a própria review, a origem atual e as demais reviews de quem escreveu.
  const opcoes = lista?.items.filter((item) => item.id !== post.origem_id && item.autor.id !== post.autor.id) ?? [];

  async function corrigir(evento: FormEvent) {
    evento.preventDefault();
    if (!escolhida) {
      setFalha("Escolha a nova origem.");
      return;
    }
    setFalha("");
    if (!confirmando) {
      setConfirmando(true);
      return;
    }
    setEnviando(true);
    try {
      aoCorrigir(await trocarOrigem(post.id, escolhida.id));
    } catch (erroDaTroca) {
      // Nada é dado como concluído: a origem exibida continua a anterior.
      setFalha(erroDaTroca instanceof Error ? erroDaTroca.message : "Não foi possível corrigir a origem.");
      setConfirmando(false);
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={corrigir} aria-busy={enviando} className="space-y-4">
      <fieldset className="space-y-2" disabled={enviando}>
        <legend className="field-label">Nova origem (reviews desta música)</legend>
        {opcoes.map((item) => (
          <label key={item.id} className="flex items-start gap-3 break-words">
            <input
              type="radio"
              name="nova-origem"
              checked={escolhida?.id === item.id}
              onChange={() => { setEscolhida(item); setConfirmando(false); setFalha(""); }}
              className="mt-1.5"
            />
            <span>Review de {item.autor.name} · nota {item.nota}</span>
          </label>
        ))}
      </fieldset>
      {carregando && <p role="status" className="text-sm text-zinc-600">Carregando reviews…</p>}
      {lista && opcoes.length === 0 && !lista.temMais && !carregando && !erro && (
        <p className="text-zinc-600">Não há outra review desta música para escolher.</p>
      )}
      {erro && (
        <div className="space-y-2">
          <MensagemErro>{erro.mensagem}</MensagemErro>
          <button type="button" className="btn-secundario" onClick={() => void carregar(erro.offset)}>Recarregar reviews</button>
        </div>
      )}
      {lista?.temMais && !erro && (
        <button type="button" className="btn-secundario w-full" disabled={carregando} onClick={() => void carregar(lista.proximo)}>
          Mais reviews
        </button>
      )}
      {confirmando && escolhida && (
        <p className="selo">
          A review passa a partir da review de {escolhida.autor.name}. Os pontos já dados à corrente antiga serão
          recalculados para a nova, e os próximos também.
        </p>
      )}
      {falha && <MensagemErro>{falha}</MensagemErro>}
      <div className="flex flex-wrap items-center gap-4">
        <button type="submit" className="btn-primary" disabled={enviando}>
          {enviando ? "Corrigindo…" : confirmando ? "Confirmar correção" : "Continuar"}
        </button>
        <button type="button" className="text-sm font-semibold text-brand-700" disabled={enviando} onClick={aoCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  );
}
