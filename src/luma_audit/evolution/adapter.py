"""adapter.py - Ponte entre EquipeAria (evolutivo) e CommitKernel (deterministico)."""
from __future__ import annotations
from .aria_skills import EquipeAria, Skill
from ..swarm.commit_kernel import CommitKernel, CommitResult
from ..swarm.ledger import Ledger


class EvolutionaryAdapter:
    """Orquestra: skill propoe -> LUMA decide -> Z-bit actualiza."""

    def __init__(self, equipe: EquipeAria, kernel: CommitKernel, ledger: Ledger):
        self.equipe = equipe
        self.kernel = kernel
        self.ledger = ledger

    def commit_evolutivo(self, skill_nome: str, contexto: dict, role: str = "luz") -> CommitResult:
        skill = self.equipe.skills.get(skill_nome)
        if not skill:
            return CommitResult(False, f"skill_desconhecida:{skill_nome}", "")

        # 1. Skill PROPOE (probabilistico)
        proposta = skill.propor(contexto)
        
        # 2. CommitKernel DECIDE (deterministico)
        # O kernel verifica policy (SkillPool), sensores e head_assinada
        res = self.kernel.commit(role=role, proposta=proposta, contexto=contexto)

        # 3. EquipeAria APRENDE (evolutivo)
        # Reforca ou derruba o Z-bit da skill
        self.equipe.registrar_veredito(skill, aprovada=res.ok)

        # 4. Ledger regista o evento com o estado evolutivo
        rep = self.equipe.reputacao(skill)
        self.ledger.append("evolutivo_commit", {
            "skill": skill_nome,
            "reputacao": round(rep, 4),
            "aprovada": res.ok,
            "motivo": res.motivo,
        })

        return res
