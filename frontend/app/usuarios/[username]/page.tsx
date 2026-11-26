"use client";

import { useParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { useSessao } from "@/components/AuthProvider";
import { Avatar } from "@/components/Avatar";
import { BotaoSeguir } from "@/components/BotaoSeguir";
import { ReviewsDoPerfil } from "@/components/ReviewsDoPerfil";
import { apiPatch, type User } from "@/lib/api";
import { buscarPerfil, PERFIL_SIMULADO, type Perfil } from "@/lib/perfil";

function membroDesde(dataIso: string): string {
  return new Date(dataIso).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
}

export default function PerfilPage() {
  const { username } = useParams<{ username: string }>();
  // A key recria o componente a cada perfil: nenhum estado passa de um para outro.
  return <PerfilDe key={username} username={username} />;
}

function PerfilDe({ username }: { username: string }) {
  const { usuario, atualizarUsuario } = useSessao();
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);
  const [editando, setEditando] = useState(false);

  useEffect(() => {
    // Descarta a resposta se a pessoa já saiu deste perfil.
    let ativa = true;
    setErro("");
    buscarPerfil(username).then(
      (resposta) => {
        if (ativa) setPerfil(resposta);
      },
      (falha: Error) => {
        if (ativa) setErro(falha.message);
      },
    );
    return () => {
      ativa = false;
    };
  }, [username, tentativa]);

  function aoSalvar(novo: User) {
    // A resposta da edição não traz contadores: mantém os que já vieram.
    setPerfil((atual) => ({ ...atual, ...novo }));
    atualizarUsuario(novo);
    setEditando(false);
  }

  if (erro) {
    return (
      <div role="alert" className="rounded-2xl border border-zinc-200 bg-white p-6">
        <p className="mb-4">{erro}</p>
        <button className="btn-primary" onClick={() => setTentativa((n) => n + 1)}>
          Tentar novamente
        </button>
      </div>
    );
  }
  if (!perfil) return <p role="status" className="text-zinc-600">Carregando perfil…</p>;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center gap-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <Avatar user={perfil} tamanho="xl" />
        <div className="min-w-0 flex-1 basis-60 space-y-2">
          <h1 className="break-words text-3xl font-bold tracking-tight">{perfil.name}</h1>
          <p className="break-words text-brand-700">@{perfil.username}</p>
          {perfil.bio && <p className="whitespace-pre-wrap break-words">{perfil.bio}</p>}
          {perfil.seguidores !== undefined && (
            <p className="flex flex-wrap gap-4 text-sm">
              <span><strong>{perfil.seguidores}</strong> {perfil.seguidores === 1 ? "seguidor" : "seguidores"}</span>
              <span><strong>{perfil.seguindo}</strong> seguindo</span>
            </p>
          )}
          {perfil.reputacao !== undefined && (
            <div className="text-sm">
              <p><strong>{perfil.reputacao}</strong> de reputação</p>
              <p className="text-zinc-500">
                Pontos por curtidas e reviews derivadas nas correntes que passam pelas reviews desta pessoa. Quanto mais longe, menor a parcela.
              </p>
            </div>
          )}
          <p className="text-sm text-zinc-500">Na rede desde {membroDesde(perfil.created_at)}</p>
        </div>
        {usuario?.id !== perfil.id && perfil.eu_sigo !== undefined && (
          <BotaoSeguir perfil={perfil} aoMudar={setPerfil} />
        )}
        {usuario?.id === perfil.id && !editando && (
          <button className="btn-primary" onClick={() => setEditando(true)}>
            Editar perfil
          </button>
        )}
      </section>

      {PERFIL_SIMULADO && (
        <p className="rounded-xl border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">
          Dados de exemplo: contadores, botão de seguir e reviews abaixo não vêm do servidor.
        </p>
      )}

      {editando && (
        <FormularioPerfil perfil={perfil} aoSalvar={aoSalvar} aoCancelar={() => setEditando(false)} />
      )}

      <ReviewsDoPerfil autor={perfil} />
    </div>
  );
}

type PropsFormulario = {
  perfil: User;
  aoSalvar: (novo: User) => void;
  aoCancelar: () => void;
};

function FormularioPerfil({ perfil, aoSalvar, aoCancelar }: PropsFormulario) {
  const [name, setName] = useState(perfil.name);
  const [bio, setBio] = useState(perfil.bio);
  const [avatarUrl, setAvatarUrl] = useState(perfil.avatar_url);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    if (!name.trim()) {
      setErro("Informe um nome.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const dados = { name: name.trim(), bio, avatar_url: avatarUrl.trim() };
      aoSalvar(await apiPatch<User>("/usuarios/eu", dados));
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Não foi possível salvar.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm" aria-labelledby="titulo-edicao">
      <h2 id="titulo-edicao" className="mb-5 text-xl font-semibold">Editar perfil</h2>
      <form onSubmit={salvar} aria-busy={salvando} className="space-y-5">
        <div>
          <label htmlFor="name" className="field-label">Nome</label>
          <input id="name" required maxLength={80} value={name} onChange={(e) => setName(e.target.value)} className="field-input" />
        </div>
        <div>
          <label htmlFor="bio" className="field-label">Bio</label>
          <textarea id="bio" maxLength={280} rows={3} value={bio} onChange={(e) => setBio(e.target.value)} className="field-input resize-y" />
        </div>
        <div>
          <label htmlFor="avatar" className="field-label">Foto (endereço de uma imagem)</label>
          <input id="avatar" type="url" maxLength={300} placeholder="https://exemplo.com/foto.png" value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} className="field-input" />
        </div>
        {erro && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{erro}</p>}
        <div className="flex flex-wrap items-center gap-4">
          <button type="submit" disabled={salvando} className="btn-primary">
            {salvando ? "Salvando…" : "Salvar"}
          </button>
          <button type="button" onClick={aoCancelar} className="text-sm font-semibold text-brand-700">
            Cancelar
          </button>
        </div>
      </form>
    </section>
  );
}
