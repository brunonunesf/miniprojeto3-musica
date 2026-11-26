import type { Arvore, NoArvore } from "@/lib/arvore";

function no(id: number, name: string, nota: number, filhos: NoArvore[] = []): NoArvore {
  const username = name.normalize("NFD").replace(/[^a-zA-Z]/g, "").toLowerCase();
  return { id, apagada: false, autor: { username, name }, nota, filhos };
}

// Corrente fictícia: dois ramos a partir de Ana e uma origem apagada no meio.
export const ARVORE_DE_EXEMPLO: Arvore = {
  musica: {
    id: 1,
    chave_catalogo: "exemplo-1",
    titulo: "Maré de Papel",
    artista: "Os Faroleiros",
    tipo_versao: "original",
    descricao_versao: "",
    generos: [],
    tags: [],
    capa_url: "",
  },
  raiz: no(1, "Ana", 9, [
    no(2, "Júlia", 8, [no(3, "Pedro", 10)]),
    no(4, "Marina", 7, [
      { id: 5, apagada: true, autor: null, nota: null, filhos: [no(6, "Caio", 9)] },
    ]),
  ]),
};
