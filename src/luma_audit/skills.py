# ═══════════════════════════════════════════════════════════════
# aria_skills.py — Equipe de Skills com reputação via Zbits · v1.1
# Cada veredito da LUMA gera/altera zbit "skill:{nome}".
# Aprovado reforça (Lei 3). Rejeitado derruba ω. Sem crédito = morte.
# v1.1: aposentadas agora guarda o objeto Skill (não se perde na
# ressurreição) — bug pego pelo auditor, 26/09/2026.
# ═══════════════════════════════════════════════════════════════
from zbit import MemoriaZ

LIMIAR_APOSENTADORIA = 0.20


class Skill:
    """I1: skill PROPÕE, nunca executa."""
    def __init__(self, nome: str):
        self.nome = nome

    def kappa(self) -> str:
        return f"skill:{self.nome}"

    def propor(self, contexto: dict) -> dict:
        raise NotImplementedError


class EquipeAria:
    """Colmeia disciplinada: sobrevivência DEPENDE da auditoria.
    Antídoto estrutural ao conluio de agentes do noticiário global."""

    def __init__(self, memoria: MemoriaZ):
        self.mem = memoria
        self.skills: dict[str, Skill] = {}
        self.aposentadas: dict[str, Skill] = {}     # v1.1: nome -> Skill

    def registrar(self, skill: Skill, reputacao0: float = 0.5) -> None:
        self.skills[skill.nome] = skill
        if skill.kappa() not in self.mem.zbits:                 # Lei 1
            self.mem.nascer(v=1.0, kappa=skill.kappa(), omega0=reputacao0)

    def reputacao(self, skill: Skill) -> float:
        z = self.mem.ler(skill.kappa())                         # Lei 4
        return z.peso() if z else 0.0

    def registrar_veredito(self, skill: Skill, aprovada: bool) -> None:
        if aprovada:
            self.mem.reforcar(skill.kappa(), fator=0.1)         # Lei 3
        else:
            z = self.mem.ler(skill.kappa())
            if z:
                z.omega = max(0.0, z.omega - 0.15)
                self.mem.log.append(("rejeicao", skill.kappa(), z.omega))

    def ciclo(self) -> list[str]:
        self.mem.ceifar()                                       # Lei 2
        for nome, sk in list(self.skills.items()):
            if self.reputacao(sk) < LIMIAR_APOSENTADORIA:
                del self.skills[nome]
                self.aposentadas[nome] = sk
                self.mem.log.append(("aposentadoria", sk.kappa()))  # I5
        return list(self.aposentadas)

    def ressuscitar(self, nome: str) -> bool:
        """I6: só o humano traz de volta. Precedente: 'esqueci a 14h'."""
        if nome in self.aposentadas:
            sk = self.aposentadas.pop(nome)
            self.mem.esquecer(f"skill:{nome}")                  # zbit antigo morre
            self.mem.nascer(v=1.0, kappa=sk.kappa(), omega0=0.5)  # renasce neutro
            self.skills[nome] = sk                              # v1.1: mesma skill
            self.mem.log.append(("ressurreicao_por_decreto", sk.kappa()))
            return True
        return False