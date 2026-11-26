import { PesquisaDeMusicas } from "@/components/PesquisaDeMusicas";
import { Populares } from "@/components/Populares";

export default function MusicasPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Músicas</h1>
      <div className="painel">
        <PesquisaDeMusicas />
      </div>
      <section className="painel" aria-labelledby="titulo-populares">
        <h2 id="titulo-populares" className="text-xl font-bold">Mais avaliadas na comunidade</h2>
        <Populares limite={20} />
      </section>
    </div>
  );
}
