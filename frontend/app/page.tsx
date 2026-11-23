"use client";

import { Cartao } from "@/components/Cartao";
import { Landing } from "@/components/Landing";
import { useLogado } from "@/lib/useLogado";

export default function Home() {
  const logado = useLogado();

  if (logado === null) return null;
  if (!logado) return <Landing />;

  return (
    <div className="space-y-4">
      <h1 className="font-titulo text-3xl font-bold">Feed</h1>
      <Cartao>
        <p className="text-suave">
          Seu feed vai aparecer aqui. Siga pessoas e recomende uma música para começar.
        </p>
      </Cartao>
    </div>
  );
}
