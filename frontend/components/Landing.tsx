import { BotaoLink } from "@/components/BotaoLink";

export function Landing() {
  return (
    <section className="flex min-h-[70vh] flex-col items-center justify-center gap-6 text-center">
      <h1 className="font-titulo text-4xl font-bold leading-tight sm:text-6xl">
        De onde <span className="text-marca">veio</span> essa música?
      </h1>
      <p className="max-w-xl text-lg text-suave">
        Recomende faixas, veja de onde cada descoberta veio e reconheça quem te apresentou aquela banda.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <BotaoLink href="/registro" className="px-5 py-2.5 text-base">
          Criar conta
        </BotaoLink>
        <BotaoLink href="/login" variante="contorno" className="px-5 py-2.5 text-base">
          Entrar
        </BotaoLink>
      </div>
    </section>
  );
}
