"use client";

import { useState } from "react";

import { MensagemErro } from "@/components/MensagemErro";
import { buscarPerfil, definirSeguir, type Perfil } from "@/lib/perfil";

type Props = { perfil: Perfil; aoMudar: (novo: Perfil) => void };

export function BotaoSeguir({ perfil, aoMudar }: Props) {
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  async function alternar() {
    setEnviando(true);
    setErro("");
    try {
      await definirSeguir(perfil.username, !perfil.eu_sigo);
      // O estado e os contadores vêm do servidor, nunca de uma conta feita aqui.
      aoMudar(await buscarPerfil(perfil.username));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível concluir.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="space-y-2">
      <button className="btn-primary" disabled={enviando} aria-pressed={perfil.eu_sigo} onClick={alternar}>
        {enviando ? "Enviando…" : perfil.eu_sigo ? "Deixar de seguir" : "Seguir"}
      </button>
      {erro && <MensagemErro>{erro}</MensagemErro>}
    </div>
  );
}
