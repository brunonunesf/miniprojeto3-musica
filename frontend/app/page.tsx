"use client";

import Link from "next/link";
import { Landing } from "@/components/Landing";
import { AlbumScene } from "@/components/MusicalHeader";
import { useSessao } from "@/components/AuthProvider";

export default function Home() {
  const { usuario } = useSessao();
  if (!usuario) return <Landing />;
  return (
    <div className="album-layout home-layout">
      <AlbumScene home>
        <h2 className="home-art-title">Seu próximo<br />encontro é com<br />uma música.</h2>
      </AlbumScene>
      <section className="album-content home-content" aria-labelledby="boas-vindas">
        <p className="mb-4 text-xs font-bold uppercase tracking-widest text-brand-700">Seu espaço de descoberta musical</p>
        <h1 id="boas-vindas" className="mb-5 text-3xl font-bold tracking-tight break-words">Olá, {usuario.name}.</h1>
        <p className="mb-8 text-xl leading-relaxed text-zinc-700">Cada indicação pode ser uma nova descoberta.</p>
        <div className="home-community-card">
          <span className="home-community-icon" aria-hidden="true">♫</span>
          <h2 className="mt-4 text-lg font-bold">Comece pelas pessoas</h2>
          <p className="mt-3 mb-6 text-sm leading-relaxed text-zinc-600">Conheça quem faz parte da comunidade. Sua próxima descoberta pode começar com alguém.</p>
          <Link href="/usuarios" className="btn-primary w-full">Conhecer pessoas</Link>
        </div>
        <p className="mt-5 text-sm leading-relaxed text-zinc-600">Seu feed de recomendações está em preparação.</p>
      </section>
    </div>
  );
}
