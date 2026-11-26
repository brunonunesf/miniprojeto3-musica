"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { RamoArvore } from "@/components/RamoArvore";
import { ARVORE_SIMULADA, buscarArvore, caminhoAte, nomeNaArvore, type Arvore } from "@/lib/arvore";

export default function ArvorePage() {
  const { id } = useParams<{ id: string }>();
  return <ArvoreDaReview key={id} id={id} />;
}

function ArvoreDaReview({ id }: { id: string }) {
  const [arvore, setArvore] = useState<Arvore | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    let ativa = true;
    setErro("");
    buscarArvore(id).then(
      (resposta) => {
        if (ativa) setArvore(resposta);
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
  if (!arvore) return <p role="status" className="text-zinc-600">Carregando a árvore…</p>;

  const atual = Number(id);
  // Do mais próximo para o mais distante: quem apresentou, e quem apresentou essa pessoa.
  const origens = caminhoAte(arvore.raiz, atual).slice(0, -1).reverse();

  return (
    <div className="space-y-5">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Árvore de recomendações</h1>
        <p className="break-words text-zinc-700">{arvore.musica.titulo} — {arvore.musica.artista}</p>
      </header>

      {ARVORE_SIMULADA && (
        <p className="rounded-xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">
          Dados de exemplo: esta corrente é fictícia e não vem do servidor.
        </p>
      )}

      {origens.length > 0 && (
        <p className="break-words font-semibold text-brand-700">
          Descoberta via {origens.map(nomeNaArvore).join(" ← ")}
        </p>
      )}

      <ul aria-label="Corrente de recomendações">
        <RamoArvore no={arvore.raiz} atual={atual} exemplo={ARVORE_SIMULADA} />
      </ul>

      {arvore.raiz.filhos.length === 0 && (
        <p className="text-zinc-600">Ninguém recomendou a partir desta review ainda.</p>
      )}
    </div>
  );
}
