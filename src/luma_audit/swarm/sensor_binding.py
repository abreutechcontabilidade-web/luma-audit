"""SensorBinding - sensores assinados por HMAC + process table (L3).

MistyPilot-style: cada sensor tem processo independente.
Se falha, e marcado Inactive e o commit recusa (fail-closed).
Stdlib puro.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class SensorRead:
    nome: str
    valor: float
    ts: float
    assinatura: str


class SensorBinding:
    """Assina leituras de sensor. Sem assinatura valida, commit recusa."""

    def __init__(self, chave: bytes):
        self.chave = chave
        self.estado: dict[str, str] = {}

    def _assinar(self, nome: str, valor: float, ts: float) -> str:
        msg = f"{nome}:{valor}:{ts:.6f}".encode("utf-8")
        return hmac.new(self.chave, msg, hashlib.sha256).hexdigest()[:32]

    def ler(self, nome: str, valor: float) -> SensorRead:
        ts = time.time()
        sig = self._assinar(nome, valor, ts)
        self.estado[nome] = "Active"
        return SensorRead(nome=nome, valor=valor, ts=ts, assinatura=sig)

    def validar(self, read: SensorRead, janela_s: float = 5.0) -> tuple[bool, str]:
        if self.estado.get(read.nome) != "Active":
            return False, f"sensor_inativo:{read.nome}"
        if (time.time() - read.ts) > janela_s:
            return False, f"sensor_stale:{read.nome}"
        esperado = self._assinar(read.nome, read.valor, read.ts)
        if not hmac.compare_digest(esperado, read.assinatura):
            return False, f"assinatura_invalida:{read.nome}"
        return True, "ok"

    def marcar_falha(self, nome: str) -> None:
        self.estado[nome] = "Inactive"
