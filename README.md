# Rede social de descoberta musical

Mini-projeto 3 do TRILHA, desenvolvido por **Bruno Nunes (@brunonunesf), Cecília Candeia (@cec1l14) e Daniel Dantas (@dnieldantas)**.

A proposta é descobrir e divulgar músicas pelas recomendações de outras pessoas, registrar como essas descobertas se espalham e reconhecer quem contribui para elas. Isso pode dar visibilidade a artistas pequenos e independentes.

**MeetMusic é apenas o nome provisório citado na conversa**; o grupo comentou que ele já é usado por outro site. O nome definitivo está em aberto.

## Ideias discutidas

- **Feed de reviews de músicas**, com curtidas e comentários.
- **Árvores de recomendações:** uma review publicada a partir de outra se conecta à publicação de origem.
- **Reputação:** curtidas e novas recomendações geram pontos para quem participa da corrente; a parcela diminui conforme a distância até a publicação que gerou a interação.
- **Bibliotecas pessoais:** músicas descobertas por meio de outras pessoas e músicas recomendadas pelo próprio usuário.
- **Perfis e follow:** acompanhar pessoas, suas recomendações, reputação e árvores.

Exemplo: Ana recomenda uma música; Júlia a descobre pelo post de Ana e publica uma review derivada; Pedro faz o mesmo pelo post de Júlia. A corrente fica **Ana → Júlia → Pedro**. Uma curtida no post de Pedro pode pontuar os três, com valores decrescentes. **Curtir não cria uma conexão na árvore; publicar uma review derivada cria.** A fórmula de pontuação ainda precisa ser definida pelo time.

Também foram sugeridos grupos de amigos para comparar e conversar sobre o que ouviram na semana e mensagens diretas. São possibilidades em discussão, sem compromisso de implementação nesta etapa.

## Estado inicial

Este repositório contém a base oficial do [miniprojeto 3](https://github.com/TrilhaUFPB/miniproj3) e a documentação inicial da proposta. A rede musical ainda não está implementada. O código de exemplo e os testes do núcleo foram preservados.

- Backend: FastAPI, SQLAlchemy e SQLite.
- Frontend: Next.js, TypeScript e Tailwind.
- [Decisões e pontos em aberto](DECISIONS.md).
- [Instruções originais do projeto](docs/README-base-trilha.md), [avaliação](RUBRICA.md), [catálogo](CATALOGO.md) e [guias](docs/guias/).

### Preparar o ambiente

```bash
git clone https://github.com/brunonunesf/miniprojeto3-musica.git
cd miniprojeto3-musica
cd backend && uv sync && cd ..
cd frontend && npm install && cp .env.local.example .env.local && cd ..
make check
make seed
make test
```

Rodar em dois terminais:

```bash
make dev-back   # http://localhost:8000/docs
make dev-front  # http://localhost:3000/usuarios
```

A tela de usuários é a demonstração original do esqueleto. Os detalhes estão no [guia de setup](docs/guias/00-setup.md).

## Trabalho em equipe

Cada integrante pode contribuir com código e documentação. Para implementação, o guia oficial sugere uma branch por feature e revisão por outra pessoa. As responsabilidades serão combinadas entre os três; nenhuma foi atribuída automaticamente.

Por solicitação do time, esta preparação não cria issues nem PRs. O fluxo de issues descrito nos guias fica para quando o time iniciar a implementação.

**Entrega:** 27/11/2026, conforme o material oficial. O guia de setup menciona um convite do GitHub Classroom para gerar o repositório do time. Como esse convite não foi fornecido, este repositório foi preparado na conta de Bruno; confirmem com a organização se a entrega deverá ser vinculada ou transferida para o Classroom.

## Origem da proposta

Síntese das mensagens de texto sobre música da conversa do grupo em 18 e 19/11/2026, priorizando a proposta detalhada de Daniel em 19/11. Os áudios não foram transcritos e seu conteúdo não foi inferido. O histórico privado, os áudios e os demais anexos não fazem parte do repositório.
