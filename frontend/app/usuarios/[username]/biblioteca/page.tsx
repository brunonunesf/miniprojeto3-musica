"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useSessao } from "@/components/AuthProvider";
import { ListaDeReviews } from "@/components/ListaDeReviews";
import { MensagemErro } from "@/components/MensagemErro";
import {
  buscarBiblioteca,
  buscarItens,
  LISTAS,
  mudarVisibilidade,
  type Biblioteca,
  type Lista,
  type Visibilidade,
} from "@/lib/biblioteca";
import { usePaginacao } from "@/lib/usePaginacao";

export default function BibliotecaPage() {
  const { username } = useParams<{ username: string }>();
  // A key recria a tela a cada pessoa: nenhuma lista passa de um perfil para outro.
  return <BibliotecaDe key={username} username={username} />;
}

function BibliotecaDe({ username }: { username: string }) {
  const { usuario } = useSessao();
  const [biblioteca, setBiblioteca] = useState<Biblioteca | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);
  const [aberta, setAberta] = useState<Lista>("descobertas");

  useEffect(() => {
    let ativa = true;
    setErro("");
    buscarBiblioteca(username).then(
      (resposta) => {
        if (ativa) setBiblioteca(resposta);
      },
      (falha: Error) => {
        if (ativa) setErro(falha.message);
      },
    );
    return () => {
      ativa = false;
    };
  }, [username, tentativa]);

  const minha = usuario?.username === username;
  const resumo = biblioteca?.[aberta];

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <header className="space-y-1">
        <h1 className="break-words text-3xl font-bold tracking-tight">
          {minha ? "Minha biblioteca" : `Biblioteca de @${username}`}
        </h1>
        <p className="text-zinc-600">
          Descobertas vieram de outra review; recomendações foram indicadas por conta própria. Não são favoritas.
        </p>
        <Link href={`/usuarios/${username}`} className="inline-block text-sm font-semibold text-brand-700">Ver perfil</Link>
      </header>

      {erro && (
        <div className="space-y-3">
          <MensagemErro>{erro}</MensagemErro>
          <button type="button" className="btn-primary" onClick={() => setTentativa((n) => n + 1)}>Tentar novamente</button>
        </div>
      )}
      {!biblioteca && !erro && <p role="status" className="text-zinc-600">Carregando biblioteca…</p>}

      {biblioteca && resumo && !erro && (
        <>
          <div role="group" aria-label="Listas" className="flex flex-wrap gap-3">
            {LISTAS.map(({ chave, nome }) => (
              <button
                key={chave}
                type="button"
                aria-pressed={aberta === chave}
                onClick={() => setAberta(chave)}
                className={aberta === chave ? "btn-primary" : "btn-secundario"}
              >
                {nome}
                {biblioteca[chave].total !== null && ` (${biblioteca[chave].total})`}
              </button>
            ))}
          </div>

          {minha && (
            <ControleDeVisibilidade key={`controle-${aberta}`} lista={aberta} atual={resumo.visibilidade} aoMudar={setBiblioteca} />
          )}

          {resumo.acessivel ? (
            <ItensDaLista key={`itens-${aberta}`} username={username} lista={aberta} />
          ) : (
            <p className="painel">Acesso restrito: esta lista é privada.</p>
          )}
        </>
      )}
    </div>
  );
}

function ItensDaLista({ username, lista }: { username: string; lista: Lista }) {
  const buscar = useCallback((offset: number) => buscarItens(username, lista, offset), [username, lista]);
  const itens = usePaginacao(buscar);
  const vazia = LISTAS.find((opcao) => opcao.chave === lista)?.vazia;
  return <ListaDeReviews {...itens} exemplo={false} vazio={<p className="text-zinc-600">{vazia}</p>} />;
}

type PropsControle = { lista: Lista; atual: Visibilidade; aoMudar: (nova: Biblioteca) => void };

function ControleDeVisibilidade({ lista, atual, aoMudar }: PropsControle) {
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  async function escolher(visibilidade: Visibilidade) {
    setSalvando(true);
    setErro("");
    try {
      // A tela só muda depois da confirmação do servidor.
      aoMudar(await mudarVisibilidade(lista, visibilidade));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar.");
    } finally {
      setSalvando(false);
    }
  }

  const opcoes: [Visibilidade, string][] = [["privada", "Só eu"], ["publica", "Todas as pessoas da rede"]];

  return (
    <fieldset className="space-y-2" disabled={salvando}>
      <legend className="field-label">Quem pode ver esta lista</legend>
      <div className="flex flex-wrap gap-5">
        {opcoes.map(([valor, rotulo]) => (
          <label key={valor} className="flex items-center gap-2">
            <input type="radio" name="visibilidade" checked={atual === valor} onChange={() => void escolher(valor)} />
            {rotulo}
          </label>
        ))}
      </div>
      {salvando && <p role="status" className="text-sm text-zinc-600">Salvando…</p>}
      {erro && <MensagemErro>{erro}</MensagemErro>}
    </fieldset>
  );
}
