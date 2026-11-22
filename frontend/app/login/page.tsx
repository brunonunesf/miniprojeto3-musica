"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Botao } from "@/components/Botao";
import { Campo } from "@/components/Campo";
import { Cartao } from "@/components/Cartao";
import { MensagemErro } from "@/components/MensagemErro";
import { entrar } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await entrar(username, password);
      router.push("/");
    } catch (err) {
      setErro(err instanceof Error ? err.message : "erro ao entrar");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm space-y-4">
      <h1 className="font-titulo text-3xl font-bold">Entrar</h1>

      <Cartao>
        <form onSubmit={enviar} className="space-y-3">
          <Campo
            rotulo="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
          <Campo
            rotulo="senha"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          {erro && <MensagemErro>{erro}</MensagemErro>}

          <Botao type="submit" disabled={enviando} className="w-full">
            {enviando ? "entrando..." : "entrar"}
          </Botao>
        </form>
      </Cartao>

      <p className="text-sm text-suave">
        Ainda não tem conta?{" "}
        <Link href="/registro" className="font-medium text-marca underline">
          Cadastre-se
        </Link>
      </p>
    </div>
  );
}
