import Link from "next/link";

import type { NoArvore } from "@/lib/arvore";

type Props = {
  no: NoArvore;
  atual: number;
  /** Reviews de exemplo não existem no servidor: sem links para elas. */
  exemplo: boolean;
  nivel?: number;
};

// Depois deste nível o recuo para de crescer, para caber em telas estreitas.
const NIVEL_MAXIMO_COM_RECUO = 5;

export function RamoArvore({ no, atual, exemplo, nivel = 0 }: Props) {
  const destacado = no.id === atual;
  const recuo = nivel < NIVEL_MAXIMO_COM_RECUO ? "ml-3 border-l-2 border-brand-500/40 pl-3" : "";
  return (
    <li>
      <div
        aria-current={destacado ? "true" : undefined}
        className={`rounded-xl border p-3 ${destacado ? "border-brand-500 bg-orange-50" : "border-zinc-200 bg-white"}`}
      >
        {no.apagada || !no.autor ? (
          <p className="text-sm italic text-zinc-500">Esta review não existe mais</p>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-2">
            {exemplo ? (
              <span className="break-words font-semibold">{no.autor.name}</span>
            ) : (
              <Link href={`/posts/${no.id}`} className="break-words font-semibold text-brand-700">{no.autor.name}</Link>
            )}
            {no.nota !== null && <span className="text-sm text-zinc-500">{no.nota}/10</span>}
          </div>
        )}
      </div>
      {no.filhos.length > 0 && (
        <ul className={`mt-3 space-y-3 ${recuo}`}>
          {no.filhos.map((filho) => (
            <RamoArvore key={filho.id} no={filho} atual={atual} exemplo={exemplo} nivel={nivel + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}
