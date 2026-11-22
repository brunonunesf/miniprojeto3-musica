import type { Metadata } from "next";
import Link from "next/link";
import { NavAuth } from "@/components/NavAuth";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rede Social da Trilha",
  description: "Mini-projeto 3 — troque este título pelo nome do seu nicho",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-fundo text-texto">
        <nav className="border-b border-borda bg-superficie">
          <div className="mx-auto flex max-w-3xl items-center gap-6 px-4 py-3">
            <Link href="/" className="font-titulo text-xl font-bold text-marca">
              {/* troque pelo nome/logo do seu nicho */}
              Rede da Trilha
            </Link>
            <Link href="/usuarios" className="text-sm text-suave hover:text-marca">
              Usuários
            </Link>
            <NavAuth />
          </div>
        </nav>
        <main className="mx-auto max-w-3xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
