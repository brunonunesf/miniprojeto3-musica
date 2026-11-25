"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import glyphs from "@/components/music-glyphs.json";

function LinhaMusical({ texto, segunda = false }: { texto: string; segunda?: boolean }) {
  let largura = 4;
  const letras = Array.from(texto).map(letra => {
    const glifo = glyphs[letra as keyof typeof glyphs];
    const x = largura - glifo.origin;
    largura += glifo.advance;
    return { glifo, x };
  });
  return (
    <span className={`music-line${segunda ? " music-line-second" : ""}`}>
      <svg viewBox={`0 10 ${largura + 4} 120`} style={{ width: `${(largura + 4) / 100}em` }} className="music-wordmark" aria-hidden="true" focusable="false">
        {letras.map(({ glifo, x }, index) => (
          <g key={index} transform={`translate(${x} 0)`}>
            {glifo.paths.map((path, pathIndex) => <path key={pathIndex} d={path.d} fill="none" stroke="currentColor" strokeWidth={path.width} strokeLinejoin="miter" strokeLinecap="butt" />)}
            {glifo.heads.map((head, headIndex) => <ellipse key={headIndex} {...head} fill="currentColor" />)}
          </g>
        ))}
      </svg>
    </span>
  );
}

function Nota({ dupla = false }: { dupla?: boolean }) {
  return <svg viewBox="0 0 64 80" fill="currentColor" focusable="false">
    {dupla ? <>
      <path d="M21 15 57 6v48h-4V21L25 28v36h-4Z" />
      <ellipse cx="15" cy="65" rx="11" ry="7" transform="rotate(-25 15 65)" />
      <ellipse cx="47" cy="55" rx="11" ry="7" transform="rotate(-25 47 55)" />
    </> : <>
      <path d="M36 8h4v49h-4Z" />
      <path d="M40 8c0 14 17 14 17 29-3-7-10-8-17-10Z" />
      <ellipse cx="27" cy="59" rx="13" ry="8" transform="rotate(-25 27 59)" />
    </>}
  </svg>;
}

function MusicBackdrop({ paused }: { paused: boolean }) {
  const svg = useRef<SVGSVGElement>(null);
  useEffect(() => {
    const scene = svg.current;
    if (paused) scene?.pauseAnimations();
    else if (scene?.animationsPaused()) scene.unpauseAnimations();
  }, [paused]);
  useEffect(() => {
    // Inicia após a montagem: o SVG é inserido depois da verificação da sessão.
    svg.current?.querySelectorAll("animate").forEach(animation => animation.beginElement());
  }, []);
  return <div className="album-backdrop" aria-hidden="true">
    <div className="album-orbit" />
    <svg ref={svg} className="album-staff" viewBox="0 0 600 500" fill="none" focusable="false">
      {[0, 13, 26, 39, 52].map(offset => {
        const a = `M-50 ${280 + offset}C100 ${140 + offset} 200 ${440 + offset} 360 ${275 + offset}S530 ${175 + offset} 660 ${235 + offset}`;
        const b = `M-50 ${260 + offset}C100 ${210 + offset} 200 ${360 + offset} 360 ${285 + offset}S530 ${115 + offset} 660 ${270 + offset}`;
        const c = `M-50 ${300 + offset}C100 ${175 + offset} 200 ${405 + offset} 360 ${260 + offset}S530 ${210 + offset} 660 ${225 + offset}`;
        return <path key={offset} d={a} stroke="currentColor" strokeWidth="1.4">
          <animate begin="indefinite" attributeName="d" values={`${a};${b};${c};${a}`} dur="18s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.333;0.667;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1;0.45 0 0.55 1" />
        </path>;
      })}
    </svg>
    {Array.from({ length: 6 }, (_, index) => <span key={index} className={`album-note album-note-${index + 1}`}><Nota dupla={index % 2 === 0} /></span>)}
  </div>;
}

export function AlbumScene({ children, home = false }: { children?: ReactNode; home?: boolean }) {
  const [paused, setPaused] = useState(false);
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduced(preference.matches);
    sync();
    preference.addEventListener("change", sync);
    return () => preference.removeEventListener("change", sync);
  }, []);
  return <section className={`album-art${home ? " album-art-home" : ""}`} data-paused={paused || reduced} aria-label={home ? "Seu espaço de descoberta musical" : "Novas músicas, novas conexões"}>
    <MusicBackdrop paused={paused || reduced} />
    <p className="album-label">Lado {home ? "B" : "A"} <span aria-hidden="true">/</span> Pessoas & música</p>
    <div className="album-title-area">
      {home ? children : <h1 className="music-title">
        <span className="sr-only">Novas músicas, novas conexões.</span>
        <span aria-hidden="true"><LinhaMusical texto="Novas músicas," /><LinhaMusical texto="novas conexões." segunda /></span>
      </h1>}
    </div>
    <div className="album-footer">
      <span className="album-caption">Uma indicação.<br />Um novo encontro.</span>
      <button type="button" className="motion-control" disabled={reduced} aria-pressed={paused || reduced} onClick={() => setPaused(value => !value)}>
        <span aria-hidden="true">{paused || reduced ? "▷" : "Ⅱ"}</span>
        {reduced ? "Movimento reduzido" : paused ? "Retomar animação" : "Pausar animação"}
      </button>
    </div>
  </section>;
}

export function MusicalHeader() {
  return <AlbumScene />;
}
