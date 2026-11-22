"use client";

import { useExigeLogin } from "@/lib/useExigeLogin";

export default function Home() {
  useExigeLogin();

  return (
    <div className="space-y-3">
      <h1 className="font-titulo text-3xl font-bold">Feed</h1>
      <p className="text-suave">
        Aqui nasce o feed do seu nicho (feature do núcleo). Enquanto isso, veja
        o slice de exemplo em{" "}
        <a href="/usuarios" className="text-marca underline">
          /usuarios
        </a>{" "}
        — toda feature sua imita aquele caminho.
      </p>
    </div>
  );
}
