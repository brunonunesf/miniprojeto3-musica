"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Page, Post } from "@/lib/api";

type Item = { id: number };
type Lista<T> = { items: T[]; proximo: number; temMais: boolean };

/** Junta duas páginas sem repetir itens: novas publicações deslocam o offset. */
function juntar<T extends Item>(atuais: T[], novos: T[]): T[] {
  const vistos = new Set(atuais.map((item) => item.id));
  return [...atuais, ...novos.filter((item) => !vistos.has(item.id))];
}

/** Lista paginada. `buscar` precisa ser estável entre renderizações. */
export function usePaginacao<T extends Item = Post>(buscar: (offset: number) => Promise<Page<T>>) {
  const [lista, setLista] = useState<Lista<T> | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<{ mensagem: string; offset: number } | null>(null);
  // Só a resposta do pedido mais recente vale.
  const pedido = useRef(0);

  // offset 0 recomeça a lista; os demais acrescentam. Em falha, o que já apareceu fica.
  const carregar = useCallback(async (offset: number) => {
    const atual = ++pedido.current;
    setCarregando(true);
    setErro(null);
    try {
      const pagina = await buscar(offset);
      if (atual !== pedido.current) return;
      const proximo = offset + pagina.items.length;
      setLista((anterior) => ({
        items: juntar(offset === 0 || !anterior ? [] : anterior.items, pagina.items),
        proximo,
        temMais: pagina.items.length > 0 && proximo < pagina.total,
      }));
    } catch (falha) {
      if (atual !== pedido.current) return;
      setErro({ mensagem: falha instanceof Error ? falha.message : "Não foi possível carregar a lista.", offset });
    }
    setCarregando(false);
  }, [buscar]);

  useEffect(() => {
    void carregar(0);
    return () => {
      pedido.current++;
    };
  }, [carregar]);

  /** Mostra um item recém-criado no fim, se não houver páginas por carregar antes dele. */
  const acrescentar = useCallback((item: T) => {
    setLista((atual) =>
      atual && !atual.temMais
        ? { ...atual, items: juntar(atual.items, [item]), proximo: atual.proximo + 1 }
        : atual,
    );
  }, []);

  return { lista, carregando, erro, carregar, acrescentar };
}
