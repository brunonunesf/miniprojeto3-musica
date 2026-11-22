import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & { rotulo: string };

export function Campo({ rotulo, ...props }: Props) {
  return (
    <label className="flex flex-col gap-1 text-sm text-suave">
      {rotulo}
      <input
        className="rounded-lg border border-borda bg-white px-2 py-1.5 text-texto focus:outline-none focus:ring-2 focus:ring-destaque"
        {...props}
      />
    </label>
  );
}
