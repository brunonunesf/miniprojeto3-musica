"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { sair, temToken } from "@/lib/auth";
import { useUsuarioAtual } from "@/lib/useUsuarioAtual";

export function NavAuth() {
  const router = useRouter();
  const [logado, setLogado] = useState(false);
  const usuario = useUsuarioAtual();

  useEffect(() => {
    const atualizar = () => setLogado(temToken());
    atualizar();
    window.addEventListener("auth", atualizar);
    return () => window.removeEventListener("auth", atualizar);
  }, []);

  function aoSair() {
    sair();
    router.push("/login");
  }

  if (logado) {
    return (
      <div className="ml-auto flex items-center gap-4 text-sm">
        {usuario && (
          <Link href={`/usuarios/${usuario.username}`} className="text-suave hover:text-marca">
            Meu perfil
          </Link>
        )}
        <button onClick={aoSair} className="text-suave hover:text-marca">
          Sair
        </button>
      </div>
    );
  }

  return (
    <div className="ml-auto flex gap-4 text-sm">
      <Link href="/login" className="text-suave hover:text-marca">
        Entrar
      </Link>
      <Link href="/registro" className="font-medium text-marca hover:text-marca-forte">
        Cadastrar
      </Link>
    </div>
  );
}
