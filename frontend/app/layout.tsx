import type { Metadata } from "next";
import Link from "next/link";
import { NavAuth } from "@/components/NavAuth";
import { NavUsuarios } from "@/components/NavUsuarios";
import { OndasNeon } from "@/components/OndasNeon";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rede da Trilha",
  description: "Rede social para descobrir música pelas indicações de quem você segue",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-fundo text-texto">
        <OndasNeon />
        <nav className="sticky top-0 z-20 border-b border-borda bg-superficie/70 backdrop-blur">
          <div className="mx-auto flex max-w-3xl items-center gap-6 px-4 py-3">
            <Link href="/" className="font-titulo text-xl font-bold text-marca">
              Rede da Trilha
            </Link>
            <NavUsuarios />
            <NavAuth />
          </div>
        </nav>
        <main className="relative z-10 mx-auto max-w-3xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
