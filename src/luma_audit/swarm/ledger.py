"""Ledger - event-sourcing com hash chain (L6).

Cada evento: seq, tipo, payload, hash_anterior, hash.
Replay por terceiros: recomputa hashes e verifica cadeia.
Stdlib puro.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

GENESIS = "LUMA-SWARM-GENESIS"


def _hash(seq: int, tipo: str, payload: dict, anterior: str) -> str:
    blob = json.dumps({"seq": seq, "tipo": tipo, "payload": payload,
                       "anterior": anterior}, sort_keys=True,
                      ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


@dataclass
class Evento:
    seq: int
    tipo: str
    payload: dict
    hash_anterior: str
    hash: str
    ts: float = field(default_factory=time.time)


class Ledger:
    """Event-sourcing append-only com hash chain verificavel."""

    def __init__(self, caminho: Path | str | None = None):
        self.caminho = Path(caminho) if caminho else None
        self.eventos: list[Evento] = []
        self.head = hashlib.sha256(GENESIS.encode()).hexdigest()[:32]
        if self.caminho and self.caminho.exists():
            self._carregar()

    def _carregar(self) -> None:
        dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        self.eventos = [Evento(**e) for e in dados]
        if self.eventos:
            self.head = self.eventos[-1].hash

    def _salvar(self) -> None:
        if not self.caminho:
            return
        self.caminho.write_text(
            json.dumps([asdict(e) for e in self.eventos], indent=2),
            encoding="utf-8")

    def append(self, tipo: str, payload: dict[str, Any]) -> Evento:
        seq = len(self.eventos) + 1
        h = _hash(seq, tipo, payload, self.head)
        ev = Evento(seq=seq, tipo=tipo, payload=payload,
                    hash_anterior=self.head, hash=h)
        self.eventos.append(ev)
        self.head = h
        self._salvar()
        return ev

    def verificar(self) -> bool:
        """True se a cadeia e integra (recomputa todos os hashes)."""
        anterior = hashlib.sha256(GENESIS.encode()).hexdigest()[:32]
        for ev in self.eventos:
            h = _hash(ev.seq, ev.tipo, ev.payload, anterior)
            if ev.hash != h or ev.hash_anterior != anterior:
                return False
            anterior = ev.hash
        return True
