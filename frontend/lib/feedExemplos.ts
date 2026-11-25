import type { Post } from "@/lib/api";

// Dados fictícios para ver a tela antes de a API do feed existir.
const MUSICAS = [
  ["Maré de Papel", "Os Faroleiros"],
  ["Janela Acesa", "Lia Marinho"],
  ["Rua do Sol", "Trio Cajueiro"],
  ["Vento de Agosto", "Banda Quintal"],
];
const PESSOAS = [
  ["ana", "Ana"],
  ["julia", "Júlia"],
  ["pedro", "Pedro"],
];

export const EXEMPLOS_DO_FEED: Post[] = Array.from({ length: 12 }, (_, i) => {
  const [titulo, artista] = MUSICAS[i % MUSICAS.length];
  const [username, name] = PESSOAS[i % PESSOAS.length];
  const created_at = new Date(Date.UTC(2026, 10, 24, 23 - i)).toISOString();
  const texto = i % 3 === 0 ? "" : "Texto de exemplo.";
  return {
    id: i + 1,
    texto,
    nota: 10 - (i % 5),
    tem_texto: texto !== "",
    musica: { id: i + 1, titulo, artista, versao: "original", capa_url: "" },
    autor: { id: (i % PESSOAS.length) + 1, username, name, bio: "", avatar_url: "", created_at },
    created_at,
  };
});
