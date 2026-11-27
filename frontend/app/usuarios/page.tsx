"use client";

import { useCallback } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { UserCard } from "@/components/UserCard";
import { apiGet, type Page, type User } from "@/lib/api";
import { usePaginacao } from "@/lib/usePaginacao";

const TAMANHO_PAGINA = 20;

export default function PessoasPage() {
  const buscar = useCallback(
    (offset: number) => apiGet<Page<User>>(`/usuarios?offset=${offset}&limit=${TAMANHO_PAGINA}`),
    [],
  );
  const { lista, carregando, erro, carregar } = usePaginacao(buscar);

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Pessoas</h1>
        <p className="text-zinc-600">Encontre quem apresenta a sua próxima descoberta.</p>
      </header>

      {lista && lista.items.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-2">
          {lista.items.map((pessoa) => (
            <li key={pessoa.id} className="min-w-0">
              <UserCard user={pessoa} />
            </li>
          ))}
        </ul>
      )}
      {lista && lista.items.length === 0 && !carregando && !erro && (
        <p className="text-zinc-600">Ainda não há pessoas por aqui.</p>
      )}
      {carregando && <p role="status" className="text-center text-zinc-600">Carregando pessoas…</p>}
      {erro && (
        <div className="space-y-3">
          <MensagemErro>{erro.mensagem}</MensagemErro>
          <button type="button" className="btn-primary" onClick={() => void carregar(erro.offset)}>Tentar novamente</button>
        </div>
      )}
      {lista?.temMais && !erro && (
        <button type="button" className="btn-secundario w-full" disabled={carregando} onClick={() => void carregar(lista.proximo)}>
          Mais pessoas
        </button>
      )}
    </div>
  );
}
