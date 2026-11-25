"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Page, Post } from "@/lib/api";

type Lista = { items: Post[]; proximo: number; temMais: boolean };

/** Junta duas páginas sem repetir reviews: novas publicações deslocam o offset. */
function juntar(atuais: Post[], novos: Post[]): Post[] {
  const vistos = new Set(atuais.map((post) => post.id));
  return [...atuais, ...novos.filter((post) => !vistos.has(post.id))];
}

/** Lista paginada de reviews. `buscar` precisa ser estável entre renderizações. */
export function usePaginacao(buscar: (offset: number) => Promise<Page<Post>>) {
  const [lista, setLista] = useState<Lista | null>(null);
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
      setErro({ mensagem: falha instanceof Error ? falha.message : "Não foi possível carregar as reviews.", offset });
    }
    setCarregando(false);
  }, [buscar]);

  useEffect(() => {
    void carregar(0);
    return () => {
      pedido.current++;
    };
  }, [carregar]);

  return { lista, carregando, erro, carregar };
}
