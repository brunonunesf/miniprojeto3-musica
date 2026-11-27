/** Ícone e nome da rede. O nome é texto da página, para usar a mesma fonte do restante. */
export function Marca({ grande = false }: { grande?: boolean }) {
  return (
    <span className={`inline-flex items-center ${grande ? "gap-3 text-5xl" : "gap-2 text-2xl"} font-black tracking-tight text-zinc-900`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/scuta-icone.svg" alt="" width={64} height={70} className={grande ? "h-16 w-auto" : "h-9 w-auto"} />
      scuta
    </span>
  );
}
