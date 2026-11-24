import Link from "next/link";

export default function Home() {
  return (
    <section className="space-y-4 rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8">
      <p className="text-sm font-semibold text-violet-700">Seu espaço de descoberta musical</p>
      <h1 className="text-3xl font-bold tracking-tight">Cada indicação pode ser uma nova descoberta.</h1>
      <p className="text-zinc-600">Seu feed de recomendações está em preparação. Enquanto isso, conheça as pessoas da comunidade.</p>
      <Link href="/usuarios" className="btn-primary">Conhecer pessoas</Link>
    </section>
  );
}
