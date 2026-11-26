import Link from "next/link";

import { Avatar } from "@/components/Avatar";
import { PautaDecorativa } from "@/components/PautaDecorativa";
import type { User } from "@/lib/api";

const NAVEGACAO = [
  ["/feed", "Feed"],
  ["/descobrir", "Descobrir"],
  ["/usuarios", "Pessoas"],
];

type Props = {
  usuario: User | null;
  /** Visitante confirmado: enquanto a sessão é verificada, só a marca aparece. */
  visitante: boolean;
  pathname: string;
  aoSair: () => void;
};

/** A mesma barra em todas as páginas: largura e altura não mudam entre elas. */
export function Navbar({ usuario, visitante, pathname, aoSair }: Props) {
  const entrando = pathname === "/login";
  return (
    <header className="border-b border-orange-100 bg-[#fffaf4]">
      <nav aria-label="Navegação principal" className="mx-auto flex min-h-[69px] max-w-[1400px] flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <span aria-hidden="true" className="text-2xl text-brand-500">♫</span>
          Descoberta musical
        </Link>
        <PautaDecorativa />
        {usuario && (
          <div className="order-last flex w-full justify-center gap-2 text-sm font-semibold md:order-none md:w-auto">
            {NAVEGACAO.map(([rota, nome]) => (
              <Link
                key={rota}
                href={rota}
                aria-current={pathname === rota || pathname.startsWith(`${rota}/`) ? "page" : undefined}
                className="rounded-lg px-4 py-2 aria-[current=page]:bg-orange-100"
              >
                {nome}
              </Link>
            ))}
          </div>
        )}
        <PautaDecorativa />
        <div className="flex items-center gap-4 text-sm">
          {usuario && (
            <>
              <Link href={`/usuarios/${usuario.username}`} aria-label={usuario.name} title={`Meu perfil: ${usuario.name}`} className="rounded-full">
                <Avatar user={usuario} />
              </Link>
              <button onClick={aoSair} className="font-semibold text-brand-700">Sair</button>
            </>
          )}
          {visitante && (
            <Link href={entrando ? "/registro" : "/login"} className="font-semibold text-brand-700">
              {entrando ? "Criar conta" : "Entrar"}
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
