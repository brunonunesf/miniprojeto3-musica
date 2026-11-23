import Link from "next/link";
import type { ComponentProps } from "react";

import { estiloBotao } from "@/components/Botao";

type Props = ComponentProps<typeof Link> & { variante?: "principal" | "contorno" };

const CONTORNO =
  "rounded-lg border border-destaque px-3 py-1.5 text-sm font-medium text-destaque hover:bg-destaque/10";

export function BotaoLink({ variante = "principal", className = "", ...props }: Props) {
  const estilo = variante === "principal" ? estiloBotao : CONTORNO;
  return <Link className={`${estilo} inline-block text-center ${className}`} {...props} />;
}
