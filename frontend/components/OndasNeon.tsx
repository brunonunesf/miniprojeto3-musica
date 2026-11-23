"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

import { useLogado } from "@/lib/useLogado";

type Onda = {
  cor: string;
  base: number;
  amplitude: number;
  frequencia: number;
  velocidade: number;
  fase: number;
  pulso: number;
};

type Mouse = { x: number; y: number; alvoX: number; alvoY: number; presenca: number; alvoPresenca: number };

const ONDAS: Onda[] = [
  { cor: "255,46,147", base: 0.78, amplitude: 28, frequencia: 0.006, velocidade: 0.55, fase: 0, pulso: 0.9 },
  { cor: "45,226,230", base: 0.83, amplitude: 24, frequencia: 0.008, velocidade: -0.45, fase: 1.3, pulso: 1.1 },
  { cor: "139,92,246", base: 0.88, amplitude: 30, frequencia: 0.0048, velocidade: 0.35, fase: 2.1, pulso: 0.7 },
  { cor: "255,46,147", base: 0.92, amplitude: 20, frequencia: 0.0095, velocidade: -0.6, fase: 3.4, pulso: 1.3 },
  { cor: "45,226,230", base: 0.96, amplitude: 24, frequencia: 0.0068, velocidade: 0.5, fase: 4.2, pulso: 1.0 },
];

const RAIO_DO_MOUSE = 180;
const PASSO_X = 6;

function desenhar(
  ctx: CanvasRenderingContext2D,
  largura: number,
  altura: number,
  tempo: number,
  mouse: Mouse
) {
  ctx.clearRect(0, 0, largura, altura);
  ctx.globalCompositeOperation = "lighter";
  ctx.lineJoin = "round";
  const brilho = 0.75 + 0.25 * Math.sin(tempo * 1.2);

  for (const onda of ONDAS) {
    const base = onda.base * altura;
    const pulso = 1 + 0.35 * Math.sin(tempo * onda.pulso + onda.fase);

    ctx.beginPath();
    for (let x = 0; x <= largura; x += PASSO_X) {
      const dx = x - mouse.x;
      const atracao = Math.exp(-(dx * dx) / (2 * RAIO_DO_MOUSE * RAIO_DO_MOUSE));
      let y = base + Math.sin(x * onda.frequencia + tempo * onda.velocidade + onda.fase) * onda.amplitude * pulso;
      y += (mouse.y - base) * 0.3 * atracao * mouse.presenca;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }

    ctx.lineWidth = 7;
    ctx.strokeStyle = `rgba(${onda.cor},${0.08 * brilho})`;
    ctx.stroke();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = `rgba(${onda.cor},${0.85 * brilho})`;
    ctx.stroke();
  }
}

function CanvasOndas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const reduzirMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const mouse: Mouse = { x: -1000, y: 0, alvoX: -1000, alvoY: 0, presenca: 0, alvoPresenca: 0 };
    let largura = 0;
    let altura = 0;
    let quadro = 0;
    const inicio = performance.now();

    function ajustarTamanho() {
      if (!canvas || !ctx) return;
      const escala = Math.min(window.devicePixelRatio || 1, 1.5);
      largura = window.innerWidth;
      altura = window.innerHeight;
      canvas.width = largura * escala;
      canvas.height = altura * escala;
      ctx.setTransform(escala, 0, 0, escala, 0, 0);
      if (reduzirMovimento) desenhar(ctx, largura, altura, 2, mouse);
    }

    function aoMoverPonteiro(e: PointerEvent) {
      mouse.alvoX = e.clientX;
      mouse.alvoY = e.clientY;
      mouse.alvoPresenca = 1;
    }

    function aoSairDaJanela() {
      mouse.alvoPresenca = 0;
    }

    function animar(agora: number) {
      if (!ctx) return;
      mouse.x += (mouse.alvoX - mouse.x) * 0.08;
      mouse.y += (mouse.alvoY - mouse.y) * 0.08;
      mouse.presenca += (mouse.alvoPresenca - mouse.presenca) * 0.06;
      desenhar(ctx, largura, altura, (agora - inicio) / 1000, mouse);
      quadro = requestAnimationFrame(animar);
    }

    ajustarTamanho();
    window.addEventListener("resize", ajustarTamanho);
    if (!reduzirMovimento) {
      window.addEventListener("pointermove", aoMoverPonteiro);
      document.addEventListener("mouseleave", aoSairDaJanela);
      quadro = requestAnimationFrame(animar);
    }

    return () => {
      cancelAnimationFrame(quadro);
      window.removeEventListener("resize", ajustarTamanho);
      window.removeEventListener("pointermove", aoMoverPonteiro);
      document.removeEventListener("mouseleave", aoSairDaJanela);
    };
  }, []);

  return <canvas ref={canvasRef} aria-hidden className="pointer-events-none fixed inset-0 -z-10 h-full w-full" />;
}

export function OndasNeon() {
  const pathname = usePathname();
  const logado = useLogado();

  const visivel = pathname === "/login" || pathname === "/registro" || (pathname === "/" && logado === false);

  return visivel ? <CanvasOndas /> : null;
}
