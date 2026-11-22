"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Botao } from "@/components/Botao";
import { Campo } from "@/components/Campo";
import { Cartao } from "@/components/Cartao";
import { MensagemErro } from "@/components/MensagemErro";
import { apiPost, type User } from "@/lib/api";
import { entrar } from "@/lib/auth";

export default function RegistroPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await apiPost<User>("/auth/registro", { username, name, password });
      await entrar(username, password);
      router.push("/");
    } catch (err) {
      setErro(err instanceof Error ? err.message : "erro ao cadastrar");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm space-y-4">
      <h1 className="font-titulo text-3xl font-bold">Criar conta</h1>

      <Cartao>
        <form onSubmit={enviar} className="space-y-3">
          <Campo
            rotulo="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            pattern="[a-z0-9_]{3,30}"
            title="3–30 caracteres: letras minúsculas, números e _"
            autoComplete="username"
            required
          />
          <Campo
            rotulo="nome"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={80}
            autoComplete="name"
            required
          />
          <Campo
            rotulo="senha"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            maxLength={72}
            title="de 8 a 72 caracteres"
            autoComplete="new-password"
            required
          />

          {erro && <MensagemErro>{erro}</MensagemErro>}

          <Botao type="submit" disabled={enviando} className="w-full">
            {enviando ? "criando..." : "criar conta"}
          </Botao>
        </form>
      </Cartao>

      <p className="text-sm text-suave">
        Já tem conta?{" "}
        <Link href="/login" className="font-medium text-marca underline">
          Entrar
        </Link>
      </p>
    </div>
  );
}
