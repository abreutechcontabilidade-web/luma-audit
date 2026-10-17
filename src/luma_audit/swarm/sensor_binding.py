"""SensorBinding - sensores assinados por HMAC + process table (L3).

MistyPilot-style: cada sensor tem processo independente.
Fail-closed por design. A2: recusa chaves com entropia < min_bits.
"""
from __future__ import annotations

import hashlib
import hmac
import math
import time
from collections import Counter
from dataclasses import dataclass


def _entropia_bits(chave: bytes) -> float:
    """Shannon entropy * len. Aproximacao de forca total."""
    if not chave:
        return 0.0
    n = len(chave)
    freq = Counter(chave)
    H = -sum((c / n) * math.log2(c / n) for c in freq.values())
    return H * n


@dataclass
class SensorRead:
    nome: str
    valor: float
    ts: float
    assinatura: str


class SensorBinding:
    """Assina leituras. A2: chave fraca = ValueError na construcao."""

    MIN_BITS_DEFAULT = 128.0

    def __init__(self, chave: bytes, min_bits: float = None):
        if not isinstance(chave, (bytes, bytearray)):
            raise TypeError("chave deve ser bytes")
        self.chave = bytes(chave)
        lim = min_bits if min_bits is not None else self.MIN_BITS_DEFAULT
        bits = _entropia_bits(self.chave)
        if bits < lim:
            raise ValueError(f"chave fraca: {bits:.1f} bits < {lim:.0f} bits")
        self.estado: dict[str, str] = {}

    def _assinar(self, nome: str, valor: float, ts: float) -> str:
        msg = f"{nome}:{valor}:{ts:.6f}".encode("utf-8")
        return hmac.new(self.chave, msg, hashlib.sha256).hexdigest()[:32]

    def ler(self, nome: str, valor: float) -> SensorRead:
        ts = time.time()
        sig = self._assinar(nome, valor, ts)
        self.estado[nome] = "Active"
        return SensorRead(nome=nome, valor=valor, ts=ts, assinatura=sig)

    def validar(self, read: SensorRead, janela_s: float = 5.0):
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
