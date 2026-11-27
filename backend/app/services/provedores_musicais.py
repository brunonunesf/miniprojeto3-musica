"""Acesso somente às APIs oficiais. Nenhuma credencial vai ao navegador."""
import asyncio
import os
import logging
import time

import httpx

from app.schemas.catalogo_externo import FaixaExterna
from app.services.identidade_musical import versao_explicita


log = logging.getLogger("uvicorn.error")


class FonteIndisponivel(Exception):
    def __init__(self, estado="indisponivel"):
        self.estado = estado


def habilitado(servico: str) -> bool:
    return os.getenv(f"{servico.upper()}_BUSCA_VALIDADA", "false").lower() == "true"


def conferir_resposta(resposta):
    if resposta.status_code == 429:
        raise FonteIndisponivel("limite")
    if resposta.status_code in (401, 403):
        raise FonteIndisponivel("sem_acesso")
    resposta.raise_for_status()
    return resposta.json()


class Spotify:
    nome = "spotify"
    _token = ""
    _expira = 0.0

    async def buscar(self, q: str) -> list[FaixaExterna]:
        if not habilitado(self.nome):
            raise FonteIndisponivel("nao_habilitado")
        client_id, secret = os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET")
        if not client_id or not secret:
            raise FonteIndisponivel("sem_acesso")
        async with httpx.AsyncClient(timeout=4, follow_redirects=False) as client:
            if time.monotonic() >= self._expira:
                resposta = await client.post("https://accounts.spotify.com/api/token",
                                             auth=(client_id, secret), data={"grant_type": "client_credentials"})
                dados = conferir_resposta(resposta)
                self._token = dados["access_token"]
                self._expira = time.monotonic() + max(0, int(dados["expires_in"]) - 30)
            resposta = await client.get("https://api.spotify.com/v1/search",
                                        params={"q": q, "type": "track", "limit": 10, "market": "BR"},
                                        headers={"Authorization": f"Bearer {self._token}"})
            if resposta.status_code == 401:
                self._expira = 0
            dados = conferir_resposta(resposta)
            return [self.normalizar(x) for x in dados["tracks"]["items"]]

    @staticmethod
    def normalizar(x):
        tipo, versao = versao_explicita(x["name"])
        imagens = x.get("album", {}).get("images", [])
        return FaixaExterna(
            servico="spotify", id_externo=x["id"], url=x["external_urls"]["spotify"],
            titulo=x["name"], artistas=[a["name"] for a in x["artists"]],
            album=x.get("album", {}).get("name", ""), duracao_ms=x.get("duration_ms"),
            isrc=(x.get("external_ids") or {}).get("isrc", ""), tipo_versao=tipo,
            descricao_versao=versao, capa_url=imagens[0]["url"] if imagens else None,
        )


class Deezer:
    nome = "deezer"

    async def buscar(self, q: str) -> list[FaixaExterna]:
        if not habilitado(self.nome):
            raise FonteIndisponivel("nao_habilitado")
        async with httpx.AsyncClient(timeout=4, follow_redirects=False) as client:
            dados = conferir_resposta(await client.get("https://api.deezer.com/search/track", params={"q": q, "limit": 10}))
            if "error" in dados:
                raise FonteIndisponivel("sem_acesso")
            # A busca não garante ISRC/contributors; detalhe oficial fornece esses campos.
            async def detalhe(x):
                identificador = str(x["id"])
                if not identificador.isdigit():
                    raise ValueError("id Deezer inválido")
                d = conferir_resposta(await client.get(f"https://api.deezer.com/track/{identificador}"))
                if "error" in d:
                    raise FonteIndisponivel()
                return self.normalizar(d)
            return await asyncio.gather(*(detalhe(x) for x in dados["data"][:10]))

    @staticmethod
    def normalizar(x):
        tipo, versao = versao_explicita(x["title"], x.get("title_version", ""))
        artistas = x.get("contributors") or [x["artist"]]
        return FaixaExterna(
            servico="deezer", id_externo=str(x["id"]), url=x["link"], titulo=x["title"],
            artistas=[a["name"] for a in artistas], album=x.get("album", {}).get("title", ""),
            duracao_ms=x["duration"] * 1000 if x.get("duration") else None,
            isrc=x.get("isrc", ""), tipo_versao=tipo, descricao_versao=versao,
            capa_url=x.get("album", {}).get("cover_medium") or None,
        )


PROVEDORES = [Spotify(), Deezer()]


async def buscar_fontes(q: str):
    async def executar(provedor):
        try:
            # Prazo global também limita a sequência token/busca ou busca/detalhe.
            faixas = await asyncio.wait_for(provedor.buscar(q), timeout=6)
            return provedor.nome, "disponivel", faixas
        except FonteIndisponivel as erro:
            log.info("busca_musical fonte=%s estado=%s", provedor.nome, erro.estado)
            return provedor.nome, erro.estado, []
        except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError):
            log.warning("busca_musical fonte=%s estado=indisponivel", provedor.nome)
            return provedor.nome, "indisponivel", []
    return await asyncio.gather(*(executar(p) for p in PROVEDORES))
