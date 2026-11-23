"use client";

import { useEffect, useState } from "react";

import { temToken } from "@/lib/auth";

export function useLogado(): boolean | null {
  const [logado, setLogado] = useState<boolean | null>(null);

  useEffect(() => {
    const atualizar = () => setLogado(temToken());
    atualizar();
    window.addEventListener("auth", atualizar);
    return () => window.removeEventListener("auth", atualizar);
  }, []);

  return logado;
}
