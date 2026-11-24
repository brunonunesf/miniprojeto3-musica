"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { MusicalHeader } from "@/components/MusicalHeader";
import { useSessao } from "@/components/AuthProvider";
import { ApiError, apiPost } from "@/lib/api";

type Campos = "username" | "name" | "password";

export function AuthForm({ registro = false }: { registro?: boolean }) {
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [mostrar, setMostrar] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erros, setErros] = useState<Partial<Record<Campos, string>>>({});
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const trava = useRef(false);
  const form = useRef<HTMLFormElement>(null);
  const { entrar } = useSessao();
  const router = useRouter();

  useEffect(() => {
    if (!registro) {
      const params = new URLSearchParams(window.location.search);
      setUsername(params.get("usuario") ?? "");
      if (params.get("contaCriada") === "1") setAviso("Conta criada. Entre para continuar.");
    }
  }, [registro]);

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (trava.current) return;
    setErro("");
    const campos: Partial<Record<Campos, string>> = {};
    if (!username) campos.username = "Informe seu usuário.";
    if (!password) campos.password = "Informe sua senha.";
    if (registro) {
      if (!/^[a-z0-9_]{3,30}$/.test(username)) campos.username = "Use de 3 a 30 letras minúsculas, números ou _.";
      if (!name.trim() || name.trim().length > 80) campos.name = "Informe um nome de 1 a 80 caracteres.";
      if (Array.from(password).length < 8) campos.password = "Use pelo menos 8 caracteres.";
    }
    if (new TextEncoder().encode(password).length > 72) campos.password = "A senha deve ter até 72 bytes. Acentos e emojis ocupam mais de um byte.";
    setErros(campos);
    if (Object.keys(campos).length) {
      form.current?.querySelector<HTMLInputElement>(`[name="${Object.keys(campos)[0]}"]`)?.focus();
      return;
    }
    trava.current = true;
    setEnviando(true);
    let contaCriada = false;
    try {
      if (registro) {
        await apiPost("/auth/registro", { username, name: name.trim(), password });
        contaCriada = true;
      }
      await entrar(username, password);
      router.replace("/");
    } catch (error) {
      if (contaCriada) {
        router.replace(`/login?contaCriada=1&usuario=${encodeURIComponent(username)}`);
        return;
      }
      if (error instanceof ApiError) {
        if (error.status === 409) setErros({ username: "Esse usuário já está em uso. Escolha outro." });
        else if (error.status === 401) setErro("Usuário ou senha inválidos.");
        else { setErros(error.fields); setErro(error.message); }
      } else setErro(error instanceof Error ? error.message : "Não foi possível continuar. Tente novamente.");
    } finally {
      trava.current = false;
      setEnviando(false);
    }
  }

  return (
    <div className={registro ? "mx-auto max-w-md" : "album-layout"}>
      {registro ? (
        <div className="mb-8 text-center">
          <p className="mb-3 text-xs font-bold uppercase tracking-widest text-brand-700">Música conecta pessoas</p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Sua próxima descoberta começa aqui</h1>
          <p className="mt-3 text-zinc-600">Descubra músicas pelas pessoas.</p>
        </div>
      ) : (
        <MusicalHeader />
      )}
      <div className={registro ? undefined : "album-content"}>
        {!registro && <p className="mb-5 text-center text-lg font-normal text-zinc-700">Bom ter você por aqui</p>}
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm sm:p-8" aria-labelledby="titulo-form">
          <h2 id="titulo-form" className="mb-6 text-xl font-semibold">{registro ? "Crie sua conta" : "Entre na sua conta"}</h2>
          {aviso && <p role="status" className="mb-5 rounded-lg bg-orange-50 p-3 text-sm text-orange-900">{aviso}</p>}
          {erro && <p role="alert" className="mb-5 rounded-lg bg-red-50 p-3 text-sm text-red-800">{erro}</p>}
          <form ref={form} onSubmit={enviar} noValidate aria-busy={enviando} className="space-y-5">
            {registro && <div>
              <label htmlFor="name" className="field-label">Nome</label>
              <input id="name" name="name" autoComplete="name" required maxLength={80} value={name} onChange={e => setName(e.target.value)} className="field-input" aria-invalid={!!erros.name} aria-describedby={erros.name ? "name-erro" : undefined} />
              {erros.name && <p id="name-erro" className="field-error" role="alert">{erros.name}</p>}
            </div>}
            <div>
              <label htmlFor="username" className="field-label">Usuário</label>
              <input id="username" name="username" autoComplete="username" autoCapitalize="none" spellCheck={false} required value={username} onChange={e => setUsername(e.target.value)} className="field-input" aria-invalid={!!erros.username} aria-describedby={erros.username ? "username-erro" : registro ? "username-ajuda" : undefined} />
              {erros.username ? <p id="username-erro" className="field-error" role="alert">{erros.username}</p> : registro ? <p id="username-ajuda" className="mt-2 text-xs text-zinc-500">De 3 a 30 letras minúsculas, números ou _.</p> : null}
            </div>
            <div>
              <label htmlFor="password" className="field-label">Senha</label>
              <div className="relative">
                <input id="password" name="password" type={mostrar ? "text" : "password"} autoComplete={registro ? "new-password" : "current-password"} required value={password} onChange={e => setPassword(e.target.value)} className="field-input pr-24" aria-invalid={!!erros.password} aria-describedby={erros.password ? "password-erro" : registro ? "password-ajuda" : undefined} />
                <button type="button" aria-controls="password" aria-pressed={mostrar} aria-label={mostrar ? "Ocultar senha" : "Mostrar senha"} onClick={() => setMostrar(!mostrar)} className="absolute inset-y-1 right-1 rounded-md px-3 text-sm font-semibold text-brand-700">{mostrar ? "Ocultar" : "Mostrar"}</button>
              </div>
              {erros.password ? <p id="password-erro" className="field-error" role="alert">{erros.password}</p> : registro ? <p id="password-ajuda" className="mt-2 text-xs text-zinc-500">Pelo menos 8 caracteres, até 72 bytes. Acentos e emojis ocupam mais de um byte.</p> : null}
            </div>
            <button type="submit" disabled={enviando} className="btn-primary w-full">{enviando ? registro ? "Criando conta…" : "Entrando…" : registro ? "Criar conta" : "Entrar"}</button>
          </form>
          <p className="mt-6 text-center text-sm text-zinc-600">{registro ? "Já tem uma conta? " : "Ainda não tem conta? "}<Link className="font-semibold text-brand-700 underline-offset-4 hover:underline" href={registro ? "/login" : "/registro"}>{registro ? "Entrar" : "Criar conta"}</Link></p>
        </section>
        {registro && <p className="mt-6 text-center text-xs text-zinc-500">Indicações de gente para gente. Novas músicas, novas conexões.</p>}
      </div>
    </div>
  );
}
