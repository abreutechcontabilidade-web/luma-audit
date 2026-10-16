"""SENTINELA - contador de dias com focos + hash chain.

Portado de teste_bender_ver/contador.py para luma-audit 0.4.0.
Stdlib puro. Sem dependencias externas.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path

GENESIS = "SENTINELA-GENESIS"
_MAX_EVENTOS = 365


def _caminho_default() -> Path:
    base = Path.home() / ".luma"
    base.mkdir(parents=True, exist_ok=True)
    return base / "sentinela.json"


class Sentinela:
    """Contador deterministico de dias com foco + hash chain auditavel."""

    def __init__(self, caminho: Path | str | None = None):
        self.caminho = Path(caminho) if caminho else _caminho_default()
        self.dados = self._carregar()

    def _carregar(self) -> dict:
        if self.caminho.exists():
            with open(self.caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "criado_em": datetime.now().isoformat(timespec="seconds"),
            "ultimo_dia": None,
            "n_dias_com_focos": 0,
            "sequencia_atual": 0,
            "sequencia_maxima": 0,
            "eventos": [],
            "hash_anterior": hashlib.sha256(GENESIS.encode()).hexdigest()[:16],
        }

    def _salvar(self) -> None:
        with open(self.caminho, "w", encoding="utf-8") as f:
            json.dump(self.dados, f, indent=2, ensure_ascii=False)

    def registrar_foco(self, motivo: str = "interacao") -> bool:
        """Registra foco de hoje. False se ja foi registado hoje."""
        hoje = date.today().isoformat()
        if self.dados["ultimo_dia"] == hoje:
            return False
        if self.dados["ultimo_dia"]:
            ultimo = date.fromisoformat(self.dados["ultimo_dia"])
            delta = (date.today() - ultimo).days
            self.dados["sequencia_atual"] = self.dados["sequencia_atual"] + 1 if delta == 1 else 1
        else:
            self.dados["sequencia_atual"] = 1
        if self.dados["sequencia_atual"] > self.dados["sequencia_maxima"]:
            self.dados["sequencia_maxima"] = self.dados["sequencia_atual"]
        self.dados["n_dias_com_focos"] += 1
        self.dados["ultimo_dia"] = hoje
        payload = f"{self.dados['hash_anterior']}|{hoje}|{motivo}|{self.dados['n_dias_com_focos']}"
        ev = {
            "dia": hoje,
            "motivo": motivo,
            "n": self.dados["n_dias_com_focos"],
            "hash_anterior": self.dados["hash_anterior"],
            "hash": hashlib.sha256(payload.encode()).hexdigest()[:16],
        }
        self.dados["hash_anterior"] = ev["hash"]
        self.dados["eventos"].append(ev)
        if len(self.dados["eventos"]) > _MAX_EVENTOS:
            self.dados["eventos"] = self.dados["eventos"][-_MAX_EVENTOS:]
        self._salvar()
        return True

    def status(self) -> dict:
        return {
            "n_dias_com_focos": self.dados["n_dias_com_focos"],
            "sequencia_atual": self.dados["sequencia_atual"],
            "sequencia_maxima": self.dados["sequencia_maxima"],
            "ultimo_dia": self.dados["ultimo_dia"],
            "hash_atual": self.dados["hash_anterior"],
        }

    def verificar_hoje(self) -> bool:
        return self.dados["ultimo_dia"] == date.today().isoformat()

    def verificar_cadeia(self) -> bool:
        """True se a hash chain esta integra."""
        prev = hashlib.sha256(GENESIS.encode()).hexdigest()[:16]
        for ev in self.dados["eventos"]:
            payload = f"{prev}|{ev['dia']}|{ev['motivo']}|{ev['n']}"
            esperado = hashlib.sha256(payload.encode()).hexdigest()[:16]
            if ev["hash"] != esperado or ev["hash_anterior"] != prev:
                return False
            prev = ev["hash"]
        return True
