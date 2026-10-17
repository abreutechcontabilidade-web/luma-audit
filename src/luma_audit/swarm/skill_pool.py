"""SkillPool - roles -> skills -> tools -> limits (L4).

Skilder-style. A3: scope obrigatorio (isolamento multi-tenant).
"""
from __future__ import annotations

from dataclasses import dataclass, field


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
    """Pool determinista com scope (A3)."""

    def __init__(self, scope: str = "default"):
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError("scope obrigatorio (string nao vazia)")
        self.scope = scope.strip()
        self.roles: dict[str, Role] = {}

    def registar_role(self, role: Role) -> None:
        self.roles[role.nome] = role

    def obter_skill(self, role: str, skill: str) -> Skill | None:
        r = self.roles.get(role)
        if not r:
            return None
        return r.skills.get(skill)

    def validar(self, role: str, proposta: dict) -> tuple[bool, str]:
        skill_nome = proposta.get("skill")
        valor = proposta.get("valor")
        if skill_nome is None:
            return False, "skill_ausente"
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            return False, "valor_invalido"
        s = self.obter_skill(role, skill_nome)
        if s is None:
            return False, f"skill_nao_autorizada:{self.scope}:{role}:{skill_nome}"
        lo, hi = s.limites
        if not (lo <= valor <= hi):
            return False, f"fora_limite:{valor}"
        return True, "ok"

    @classmethod
    def default(cls, scope: str = "default") -> "SkillPool":
        p = cls(scope=scope)
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

    @classmethod
    def for_tenant(cls, scope: str) -> "SkillPool":
        return cls.default(scope=scope)
