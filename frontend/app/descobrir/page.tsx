import Link from "next/link";

export default function DescobrirPage() {
  return (
    <section className="painel space-y-4">
      <h1 className="text-3xl font-bold tracking-tight">Descobrir para você</h1>
      <p className="text-zinc-700">As sugestões a partir das suas reviews e curtidas ainda estão em preparação.</p>
      <Link href="/musicas" className="btn-primary">Pesquisar músicas</Link>
    </section>
  );
}
