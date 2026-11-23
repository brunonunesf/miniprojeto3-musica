"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { BotaoLink } from "@/components/BotaoLink";
import { sair } from "@/lib/auth";
import { useLogado } from "@/lib/useLogado";
import { useUsuarioAtual } from "@/lib/useUsuarioAtual";

export function NavAuth() {
  const router = useRouter();
  const logado = useLogado() === true;
  const usuario = useUsuarioAtual();

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
    <div className="ml-auto flex items-center gap-4 text-sm">
      <Link href="/login" className="text-suave hover:text-marca">
        Entrar
      </Link>
      <BotaoLink href="/registro">Cadastrar</BotaoLink>
    </div>
  );
}
