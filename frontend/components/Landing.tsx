import Link from "next/link";

import { AlbumScene } from "@/components/MusicalHeader";

export function Landing() {
  return (
    <div className="album-layout">
      <AlbumScene />
      <section className="album-content text-center" aria-labelledby="chamada">
        <p className="mb-4 text-xs font-bold uppercase tracking-widest text-brand-700">Música conecta pessoas</p>
        <h2 id="chamada" className="mb-5 text-3xl font-bold tracking-tight sm:text-4xl">De onde veio essa música?</h2>
        <p className="mb-8 text-lg leading-relaxed text-zinc-700">
          Recomende faixas, veja de onde cada descoberta veio e reconheça quem te apresentou aquela banda.
        </p>
        <Link href="/registro" className="btn-primary w-full">Criar conta</Link>
        <p className="mt-6 text-sm text-zinc-600">
          Já tem uma conta?{" "}
          <Link href="/login" className="font-semibold text-brand-700 underline-offset-4 hover:underline">Entrar</Link>
        </p>
      </section>
    </div>
  );
}
