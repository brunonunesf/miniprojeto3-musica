"use client";

import { useEffect, useState } from "react";

import { apiGet, type User } from "@/lib/api";
import { temToken } from "@/lib/auth";

export function useUsuarioAtual(): User | null {
  const [usuario, setUsuario] = useState<User | null>(null);

  useEffect(() => {
    const carregar = () => {
      if (!temToken()) {
        setUsuario(null);
        return;
      }
      apiGet<User>("/auth/eu").then(setUsuario, () => setUsuario(null));
    };
    carregar();
    window.addEventListener("auth", carregar);
    return () => window.removeEventListener("auth", carregar);
  }, []);

  return usuario;
}
