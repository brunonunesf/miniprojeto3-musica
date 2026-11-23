import type { TextareaHTMLAttributes } from "react";

import { estiloCampo } from "@/components/Campo";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement> & { rotulo: string };

export function AreaTexto({ rotulo, ...props }: Props) {
  return (
    <label className="flex flex-col gap-1 text-sm text-suave">
      {rotulo}
      <textarea className={`${estiloCampo} resize-y`} {...props} />
    </label>
  );
}
