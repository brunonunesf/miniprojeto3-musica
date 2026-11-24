"use client";

import { useEffect, useState } from "react";
import { apiGet, type Music, type Page } from "@/lib/api";

const versoes = { original: "Original", remix: "Remix", ao_vivo: "Ao vivo", remaster: "Remaster" };

export function MusicSelector({ value, onChange }: {
  value: number | null;
  onChange: (musicaId: number, musica: Music) => void;
}) {
  const [busca, setBusca] = useState("");
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [tentativa, setTentativa] = useState(0);
  const [pagina, setPagina] = useState<Page<Music> | null>(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    let ativa = true;
    setCarregando(true);
    setErro("");
    apiGet<Page<Music>>(`/musicas?q=${encodeURIComponent(q)}&offset=${offset}&limit=10`)
      .then(dados => { if (ativa) setPagina(dados); })
      .catch((e: Error) => { if (ativa) setErro(e.message); })
      .finally(() => { if (ativa) setCarregando(false); });
    return () => { ativa = false; };
  }, [q, offset, tentativa]);

  return <section aria-label="Selecionar música">
    <form onSubmit={e => { e.preventDefault(); setQ(busca); setOffset(0); setTentativa(t => t + 1); }} className="my-6 flex flex-wrap gap-3">
      <label className="flex-1">Título ou artista
        <input className="mt-2 w-full rounded-lg border border-zinc-300 bg-white p-3" value={busca} maxLength={200} onChange={e => setBusca(e.target.value)} />
      </label>
      <button className="btn-primary self-end" type="submit">Buscar</button>
    </form>
    {carregando ? <p role="status">Carregando músicas…</p> : erro ? <div role="alert"><p>{erro}</p><button className="btn-primary mt-3" onClick={() => setTentativa(t => t + 1)}>Tentar novamente</button></div> : pagina ? <>
      <p role="status" className="mb-4 text-sm text-zinc-600">{pagina.total ? `${pagina.total} músicas encontradas` : "Nenhuma música encontrada. Tente outro título ou artista."}</p>
      <ul className="space-y-3">{pagina.items.map(musica => <li key={musica.id}>
        <button type="button" aria-pressed={value === musica.id} onClick={() => onChange(musica.id, musica)} className={`w-full rounded-xl border bg-white p-4 text-left focus-visible:outline-2 focus-visible:outline-brand-700 ${value === musica.id ? "border-brand-700 ring-2 ring-brand-500" : "border-zinc-200"}`}>
          <span className="block font-bold">{musica.titulo} — {musica.artista}</span>
          <span className="mt-1 block text-sm text-zinc-600">{versoes[musica.tipo_versao]} · {musica.descricao_versao}</span>
          <span className="mt-2 block text-xs text-zinc-600">{musica.generos.join(" · ")}</span>
          {value === musica.id && <span className="mt-2 block text-sm font-bold text-brand-700">Selecionada</span>}
        </button>
      </li>)}</ul>
      {pagina.total > 10 && <div className="mt-5 flex items-center gap-4">
        <button disabled={offset === 0} onClick={() => setOffset(n => Math.max(0, n - 10))} className="btn-primary disabled:opacity-50">Anterior</button>
        <span>Página {Math.floor(offset / 10) + 1}</span>
        <button disabled={offset + 10 >= pagina.total} onClick={() => setOffset(n => n + 10)} className="btn-primary disabled:opacity-50">Próxima</button>
      </div>}
    </> : null}
  </section>;
}
