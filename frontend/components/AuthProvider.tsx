"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { ApiError, apiGet, apiPost, type User } from "@/lib/api";

type Estado = "verificando" | "autenticado" | "visitante" | "erro";
type Sessao = {
  usuario: User | null;
  entrar: (username: string, password: string) => Promise<void>;
  atualizarUsuario: (novo: User) => void;
};
const Contexto = createContext<Sessao | null>(null);

export function useSessao() {
  const sessao = useContext(Contexto);
  if (!sessao) throw new Error("useSessao precisa de AuthProvider");
  return sessao;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<Estado>("verificando");
  const [usuario, setUsuario] = useState<User | null>(null);
  const [aviso, setAviso] = useState("");
  const versao = useRef(0);
  const pathname = usePathname();
  const router = useRouter();
  const publica = pathname === "/login" || pathname === "/registro";
  // A home atende os dois casos: apresentação para visitantes, início para quem entrou.
  const aberta = pathname === "/";
  const ampla = pathname === "/login" || pathname === "/";

  const limpar = useCallback((mensagem = "") => {
    versao.current += 1;
    setUsuario(null);
    setEstado("visitante");
    setAviso(mensagem);
  }, []);

  const expirar = useCallback(() => {
    limpar("Sua sessão não é mais válida. Entre novamente.");
    router.replace("/login");
  }, [limpar, router]);

  const verificar = useCallback(async () => {
    const atual = ++versao.current;
    setUsuario(null);
    setEstado("verificando");
    if (!localStorage.getItem("token")) {
      setEstado("visitante");
      return;
    }
    try {
      const user = await apiGet<User>("/auth/eu");
      if (atual !== versao.current) return;
      setUsuario(user);
      setEstado("autenticado");
      setAviso("");
    } catch (erro) {
      if (atual !== versao.current) return;
      if (erro instanceof ApiError && erro.status === 401) {
        expirar();
      } else {
        setEstado("erro");
      }
    }
  }, [expirar]);

  useEffect(() => {
    const storage = (event: StorageEvent) => {
      if (event.key === "token" || event.key === null) {
        if (!localStorage.getItem("token")) limpar("Você saiu da conta em outra aba.");
        else void verificar();
      }
    };
    window.addEventListener("sessao-invalida", expirar);
    window.addEventListener("storage", storage);
    void verificar();
    return () => {
      versao.current += 1;
      window.removeEventListener("sessao-invalida", expirar);
      window.removeEventListener("storage", storage);
    };
  }, [expirar, limpar, verificar]);

  useEffect(() => {
    if (estado === "visitante" && !publica && !aberta) router.replace("/login");
    if (estado === "autenticado" && publica) router.replace("/");
  }, [estado, publica, aberta, router]);

  async function entrar(username: string, password: string) {
    const atual = ++versao.current;
    const { token } = await apiPost<{ token: string }>("/auth/login", { username, password });
    if (atual !== versao.current) throw new Error("A sessão mudou. Tente entrar novamente.");
    localStorage.setItem("token", token);
    setAviso("");
    await verificar();
  }

  function atualizarUsuario(novo: User) {
    setUsuario((atual) => (atual?.id === novo.id ? novo : atual));
  }

  function sair() {
    localStorage.removeItem("token");
    limpar();
    router.replace("/login");
  }

  const liberado =
    (estado === "visitante" && (publica || aberta)) || (estado === "autenticado" && !publica);

  return (
    <Contexto.Provider value={{ usuario, entrar, atualizarUsuario }}>
      <a href="#conteudo" className="skip-link">Pular para o conteúdo</a>
      <header className="border-b border-zinc-200 bg-white">
        <nav aria-label="Navegação principal" className={`mx-auto flex ${ampla ? "max-w-[1152px]" : "max-w-3xl"} flex-wrap items-center justify-between gap-3 px-4 py-4`}>
          <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <span aria-hidden="true" className="flex size-9 items-center justify-center rounded-xl bg-brand-500 text-xl text-brand-950">♫</span>
            Descoberta musical
          </Link>
          {estado === "autenticado" && usuario ? (
            <div className="flex min-w-0 flex-wrap items-center gap-4 text-sm">
              <Link href="/" aria-current={pathname === "/" ? "page" : undefined}>Início</Link>
              <Link href="/feed" aria-current={pathname === "/feed" ? "page" : undefined}>Feed</Link>
              <Link href="/usuarios" aria-current={pathname === "/usuarios" ? "page" : undefined}>Usuários</Link>
              <Link href="/posts/novo" aria-current={pathname === "/posts/novo" ? "page" : undefined}>Nova review</Link>
              <Link href={`/usuarios/${usuario.username}`} aria-current={pathname === `/usuarios/${usuario.username}` ? "page" : undefined} className="max-w-36 truncate text-zinc-600" title={`Meu perfil: ${usuario.name}`}>{usuario.name}</Link>
              <button onClick={sair} className="font-semibold text-brand-700">Sair</button>
            </div>
          ) : estado === "visitante" ? (
            <Link href={pathname === "/login" ? "/registro" : "/login"} className="text-sm font-semibold text-brand-700">
              {pathname === "/login" ? "Criar conta" : "Entrar"}
            </Link>
          ) : null}
        </nav>
      </header>
      <main id="conteudo" className={`mx-auto ${ampla ? "max-w-[1152px]" : "max-w-3xl"} px-4 py-8 sm:py-12`}>
        {aviso && <p role="status" className="mb-6 rounded-xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">{aviso}</p>}
        {estado === "erro" ? (
          <section className="mx-auto max-w-md rounded-2xl border border-zinc-200 bg-white p-6" aria-labelledby="erro-sessao">
            <h1 id="erro-sessao" className="text-xl font-semibold">Não conseguimos verificar sua sessão</h1>
            <p className="my-4 text-zinc-600">Confira sua conexão e tente novamente. Sua sessão foi mantida neste dispositivo.</p>
            <button className="btn-primary" onClick={() => void verificar()}>Tentar novamente</button>
            <button className="ml-4 text-sm font-semibold text-brand-700" onClick={sair}>Sair da conta</button>
          </section>
        ) : liberado ? children : <p role="status" className="py-12 text-center text-zinc-600">Verificando sessão…</p>}
      </main>
    </Contexto.Provider>
  );
}
