"use client";

import { useEffect, useState } from "react";

/** Falso até o servidor confirmar o recurso. `consultar` precisa ser estável entre renderizações. */
export function useDisponivel(consultar: () => Promise<boolean>): boolean {
  const [disponivel, setDisponivel] = useState(false);
  useEffect(() => {
    let ativa = true;
    void consultar().then((sim) => {
      if (ativa) setDisponivel(sim);
    });
    return () => {
      ativa = false;
    };
  }, [consultar]);
  return disponivel;
}
