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
  const created_at = new Date(Date.now() - (i * 25 + 12) * 60_000).toISOString();
  const texto = i % 3 === 0 ? "" : "Texto de exemplo.";
  return {
    id: i + 1,
    texto,
    nota: 10 - (i % 5),
    tem_texto: texto !== "",
    musica: {
      id: i + 1,
      chave_catalogo: `exemplo-${i + 1}`,
      titulo,
      artista,
      tipo_versao: "original",
      descricao_versao: "",
      generos: [],
      tags: [],
      capa_url: "",
    },
    autor: { id: (i % PESSOAS.length) + 1, username, name, bio: "", avatar_url: "", created_at },
    created_at,
    curtidas: 12 - (i % 7),
    curtido_por_mim: false,
    origem: i === 0 ? { id: 2, autor: { name: "Júlia" } } : null,
  };
});
