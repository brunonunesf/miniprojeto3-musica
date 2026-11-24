# Identidade musical

Direção aprovada por Bruno: laranja claro, fundo neutro/creme, Merriweather para textos e um alfabeto geométrico próprio para o título musical.

## Alfabeto aprovado

- [Maiúsculas A–Z](alfabeto-maiusculas.svg).
- [Minúsculas a–z](alfabeto-minusculas.svg).
- [Amostra em palavras](amostra-em-palavras.svg).

As letras são desenhos vetoriais originais construídos com hastes, barras e cabeças de notas. A imagem fornecida na conversa serviu de referência de linguagem visual; não é distribuída no repositório.

`frontend/components/music-glyphs.json` contém os 52 desenhos, espaço, vírgula, ponto e os acentos ú/õ usados no título. Os dados de hastes, elipses e espaçamento são renderizados como SVG em `MusicalHeader.tsx`. Não é uma fonte TTF/WOFF, e os campos/formulários continuam usando Merriweather.

## Paleta e movimento

| Uso | Cor |
|---|---|
| Botões e detalhes | `#f58220` |
| Hover | `#e67412` |
| Títulos e links | `#ad4c00` |
| Texto dos botões | `#431d08` |
| Área artística | `#fffaf4` |

O login revela duas linhas continuamente, sem digitação. As pautas ondulam e as notas flutuam lentamente. O botão Pausar/Retomar controla o movimento; a preferência de movimento reduzido desativa a entrada e mantém a arte estática. O cadastro conserva sua composição simples.

As capturas e gravações de validação são resultados locais, não arquivos necessários à aplicação. Detalhes de produto, limites e autoria estão em `DECISIONS.md`.
