import type { HTMLAttributes } from "react";

export function Cartao({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-xl border border-borda bg-superficie p-4 ${className}`}
      {...props}
    />
  );
}
