"""Seleção temporária autenticada, sem gravar resultados de busca no banco."""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.catalogo_externo import FaixaExterna


def _chave():
    chave = os.getenv("MUSICA_SELECTION_SECRET", "")
    if len(chave.encode()) < 32:
        raise HTTPException(503, "Seleção externa indisponível: configure a chave de assinatura.")
    return chave.encode()


def assinar(faixas: list[FaixaExterna], usuario_id: int) -> str:
    payload = json.dumps({"v": 1, "usuario": usuario_id, "exp": int(time.time()) + 900,
                          "faixas": [f.model_dump(mode="json") for f in faixas]}, separators=(",", ":"))
    corpo = base64.urlsafe_b64encode(payload.encode()).decode()
    assinatura = hmac.new(_chave(), corpo.encode(), hashlib.sha256).hexdigest()
    return f"{corpo}.{assinatura}"


def verificar(token: str, usuario_id: int) -> list[FaixaExterna]:
    try:
        corpo, assinatura = token.rsplit(".", 1)
        esperada = hmac.new(_chave(), corpo.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperada, assinatura):
            raise ValueError()
        dados = json.loads(base64.b64decode(corpo + "=" * (-len(corpo) % 4), altchars=b"-_", validate=True))
        if dados["v"] != 1 or dados["usuario"] != usuario_id or dados["exp"] <= time.time():
            raise ValueError()
        faixas = [FaixaExterna.model_validate(f) for f in dados["faixas"]]
        if not 1 <= len(faixas) <= 20:
            raise ValueError()
        return faixas
    except (ValueError, KeyError, TypeError, ValidationError):
        raise HTTPException(422, "Seleção inválida ou expirada. Busque e selecione a música novamente.")
