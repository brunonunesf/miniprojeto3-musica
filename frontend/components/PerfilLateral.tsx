"use client";

import Link from "next/link";

import { useSessao } from "@/components/AuthProvider";
import { Avatar } from "@/components/Avatar";

function Icone({ children }: { children: string }) {
  return <span aria-hidden="true" className="w-5 text-center text-lg text-brand-700">{children}</span>;
}

export function PerfilLateral() {
  const { usuario } = useSessao();
  if (!usuario) return null;
  const perfil = `/usuarios/${usuario.username}`;

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Avatar user={usuario} tamanho="xl" />
        <p className="break-words text-xl font-bold">{usuario.name}</p>
        <p className="break-words text-sm text-zinc-600">@{usuario.username}</p>
        <Link href={perfil} className="text-sm font-semibold text-brand-700">Ver meu perfil</Link>
      </div>
      <ul className="space-y-1 border-y border-zinc-200 py-4 text-sm">
        <li><Link href="/feed" aria-current="page" className="item-lateral bg-orange-50"><Icone>⌂</Icone>Meu feed</Link></li>
        <li><Link href={`${perfil}/biblioteca`} className="item-lateral"><Icone>▤</Icone>Minha biblioteca</Link></li>
        <li><Link href={perfil} className="item-lateral"><Icone>✎</Icone>Minhas reviews</Link></li>
      </ul>
      <Link href="/posts/novo" className="btn-primary w-full">+ Escrever review</Link>
      <p className="text-sm italic text-zinc-600">Cada indicação pode ser uma nova descoberta.</p>
    </div>
  );
}
