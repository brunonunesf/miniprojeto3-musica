"use client";

import Link from "next/link";

import { useLogado } from "@/lib/useLogado";

export function NavUsuarios() {
  if (useLogado() !== true) return null;

  return (
    <Link href="/usuarios" className="text-sm text-suave hover:text-marca">
      Usuários
    </Link>
  );
}
