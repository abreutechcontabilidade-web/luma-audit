"""CommitKernel - fronteira determinista (L5).

DASC-style: policy + provenance + authority + state.
Nada executa sem passar por aqui. Fail-closed por design.
Registra tudo no Ledger (L6).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ledger import Ledger
from .sensor_binding import SensorBinding, SensorRead
from .skill_pool import SkillPool


@dataclass
class CommitResult:
    ok: bool
    motivo: str
    evento_hash: str


class CommitKernel:
    """Valida e registra commits. Determinista."""

    def __init__(self, pool: SkillPool, sensors: SensorBinding,
                 ledger: Ledger):
        self.pool = pool
        self.sensors = sensors
        self.ledger = ledger

    def commit(self, role: str, proposta: dict[str, Any],
               contexto: dict[str, Any]) -> CommitResult:
        # 1. pool autoriza?
        ok, motivo = self.pool.validar(role, proposta)
        if not ok:
            ev = self.ledger.append("commit_rejeitado",
                                    {"role": role, "proposta": proposta,
                                     "motivo": motivo})
            return CommitResult(False, motivo, ev.hash)

        # 2. sensores validos?
        sensor_nome = contexto.get("sensor_nome")
        sensor_valor = contexto.get("sensor_valor")
        sensor_ts = contexto.get("sensor_ts")
        sensor_sig = contexto.get("sensor_sig")
        if not all([sensor_nome, sensor_valor is not None,
                    sensor_ts is not None, sensor_sig]):
            ev = self.ledger.append("commit_rejeitado",
                                    {"role": role, "motivo": "sensor_ausente"})
            return CommitResult(False, "sensor_ausente", ev.hash)

        read = SensorRead(nome=sensor_nome, valor=sensor_valor,
                          ts=sensor_ts, assinatura=sensor_sig)
        ok_s, motivo_s = self.sensors.validar(read)
        if not ok_s:
            ev = self.ledger.append("commit_rejeitado",
                                    {"role": role, "motivo": motivo_s})
            return CommitResult(False, motivo_s, ev.hash)

        # 3. tudo OK - registra
        ev = self.ledger.append("commit_aprovado",
                                {"role": role, "proposta": proposta,
                                 "sensor": sensor_nome})
        return CommitResult(True, "ok", ev.hash)
