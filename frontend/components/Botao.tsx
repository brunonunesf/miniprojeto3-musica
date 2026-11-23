import type { ButtonHTMLAttributes } from "react";

export const estiloBotao =
  "rounded-lg bg-marca px-3 py-1.5 text-sm font-medium text-fundo shadow-[0_0_14px_-3px_var(--color-marca)] hover:bg-marca-forte disabled:opacity-50 disabled:shadow-none";

export function Botao({ className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={`${estiloBotao} ${className}`} {...props} />;
}
