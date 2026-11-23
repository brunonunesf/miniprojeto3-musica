"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AreaTexto } from "@/components/AreaTexto";
import { Avatar } from "@/components/Avatar";
import { Botao } from "@/components/Botao";
import { Campo } from "@/components/Campo";
import { Cartao } from "@/components/Cartao";
import { MensagemErro } from "@/components/MensagemErro";
import { apiGet, apiPatch, type User } from "@/lib/api";
import { useExigeLogin } from "@/lib/useExigeLogin";
import { useUsuarioAtual } from "@/lib/useUsuarioAtual";

function membroDesde(dataIso: string): string {
  return new Date(dataIso).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
}

export default function PerfilPage() {
  useExigeLogin();
  const { username } = useParams<{ username: string }>();
  const atual = useUsuarioAtual();

  const [perfil, setPerfil] = useState<User | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [editando, setEditando] = useState(false);

  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erroEdicao, setErroEdicao] = useState<string | null>(null);

  useEffect(() => {
    setPerfil(null);
    setErro(null);
    setEditando(false);
    apiGet<User>(`/usuarios/${username}`).then(setPerfil, (e: unknown) =>
      setErro(e instanceof Error ? e.message : "erro ao carregar o perfil")
    );
  }, [username]);

  const ehMeu = perfil !== null && atual?.username === perfil.username;

  function abrirEdicao() {
    if (!perfil) return;
    setName(perfil.name);
    setBio(perfil.bio);
    setAvatarUrl(perfil.avatar_url);
    setErroEdicao(null);
    setEditando(true);
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setSalvando(true);
    setErroEdicao(null);
    try {
      setPerfil(await apiPatch<User>("/usuarios/eu", { name, bio, avatar_url: avatarUrl }));
      setEditando(false);
    } catch (err) {
      setErroEdicao(err instanceof Error ? err.message : "erro ao salvar");
    } finally {
      setSalvando(false);
    }
  }

  if (erro) return <MensagemErro>{erro}</MensagemErro>;
  if (!perfil) return <p className="text-suave">carregando...</p>;

  return (
    <div className="space-y-4">
      <Cartao className="flex flex-wrap items-center gap-4">
        <Avatar user={perfil} tamanho="xl" />
        <div className="min-w-0 flex-1 space-y-1">
          <h1 className="font-titulo text-3xl font-bold">{perfil.name}</h1>
          <p className="text-suave">@{perfil.username}</p>
          {perfil.bio && <p>{perfil.bio}</p>}
          <p className="text-sm text-suave">Na rede desde {membroDesde(perfil.created_at)}</p>
        </div>
        {ehMeu && !editando && <Botao onClick={abrirEdicao}>Editar perfil</Botao>}
      </Cartao>

      {editando && (
        <Cartao>
          <form onSubmit={salvar} className="space-y-3">
            <Campo
              rotulo="nome"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={80}
              required
            />
            <AreaTexto
              rotulo="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              maxLength={280}
              rows={3}
            />
            <Campo
              rotulo="foto (endereço de uma imagem)"
              type="url"
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              maxLength={300}
              placeholder="https://exemplo.com/foto.png"
            />

            {erroEdicao && <MensagemErro>{erroEdicao}</MensagemErro>}

            <div className="flex gap-2">
              <Botao type="submit" disabled={salvando}>
                {salvando ? "salvando..." : "salvar"}
              </Botao>
              <button
                type="button"
                onClick={() => setEditando(false)}
                className="rounded-lg px-3 py-1.5 text-sm text-suave hover:text-texto"
              >
                cancelar
              </button>
            </div>
          </form>
        </Cartao>
      )}
    </div>
  );
}
