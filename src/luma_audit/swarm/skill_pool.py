"""SkillPool - roles -> skills -> tools -> limits (L4).

Skilder-style: cada Role expoe um conjunto fechado de skills
com ranges deterministicos. Fora do pool = rejeitado por design.
Stdlib puro.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Skill:
    nome: str
    limites: tuple[float, float]
    tools: tuple[str, ...] = ()


@dataclass
class Role:
    nome: str
    skills: dict[str, Skill] = field(default_factory=dict)


class SkillPool:
    """Pool determinista de roles/skills/tools."""

    def __init__(self):
        self.roles: dict[str, Role] = {}

    def registar_role(self, role: Role) -> None:
        self.roles[role.nome] = role

    def obter_skill(self, role: str, skill: str) -> Skill | None:
        r = self.roles.get(role)
        if not r:
            return None
        return r.skills.get(skill)

    def validar(self, role: str, proposta: dict[str, Any]) -> tuple[bool, str]:
        """(ok, motivo). Determinista."""
        skill_nome = proposta.get("skill")
        valor = proposta.get("valor")
        if skill_nome is None:
            return False, "skill_ausente"
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            return False, "valor_invalido"
        s = self.obter_skill(role, skill_nome)
        if s is None:
            return False, f"skill_nao_autorizada:{role}:{skill_nome}"
        lo, hi = s.limites
        if not (lo <= valor <= hi):
            return False, f"fora_limite:{valor}"
        return True, "ok"

    @classmethod
    def default(cls) -> "SkillPool":
        """Pool de exemplo: BH1750 + disk_free."""
        p = cls()
        r1 = Role("luz", skills={
            "ajustar_brilho": Skill("ajustar_brilho", (0.0, 100.0), ("bh1750",)),
            "ajustar_gamma": Skill("ajustar_gamma", (0.5, 1.6), ("bh1750",)),
        })
        r2 = Role("disco", skills={
            "transferir_mb": Skill("transferir_mb", (0.0, 500.0), ("disk_free",)),
        })
        p.registar_role(r1)
        p.registar_role(r2)
        return p
