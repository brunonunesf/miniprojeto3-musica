import type { ButtonHTMLAttributes } from "react";

export function Botao({ className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`rounded-lg bg-marca px-3 py-1.5 text-sm font-medium text-white hover:bg-marca-forte disabled:opacity-50 ${className}`}
      {...props}
    />
  );
}
