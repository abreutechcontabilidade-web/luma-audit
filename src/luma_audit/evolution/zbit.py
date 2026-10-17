# ═══════════════════════════════════════════════════════════════
# zbit.py — LUMA v6 · Unidade de memória viva · v1.1
#
# PAIS CITADOS:
#  [1] Ebbinghaus (1885), Über das Gedächtnis — R = e^(-t/S) → λ
#  [2] Friston (2010), Nature Rev. Neuroscience — precision → ω
#  [3] Kolchinsky & Wolpert (2018), J. R. Soc. Interface — aboutness → κ
#  [4] Shannon (1948), Bell System TJ — surpresa → v
#  [5] Sutton & Barto (2018), Reinforcement Learning — reforço
#
# CONTRATO DE ABSTRAÇÃO: rigor + vocabulário, não física nova.
# ═══════════════════════════════════════════════════════════════
import time
from dataclasses import dataclass

DIA = 86400.0
EPS_MORTE = 0.01


@dataclass
class Zbit:
    """Z = (v, κ, τ, ω, λ). O bit que envelhece."""
    v: float
    kappa: str
    tau: float
    omega: float = 1.0
    lam: float = 0.9

    def peso(self, agora: float | None = None) -> float:
        agora = agora if agora is not None else time.time()
        delta = max(0.0, agora - self.tau)      # v1.1: relógio nunca anda pra trás
        return self.omega * (self.lam ** (delta / DIA))

    def morto(self, agora: float | None = None) -> bool:
        return self.peso(agora) < EPS_MORTE

    def reforcar(self, fator: float = 0.1, agora: float | None = None) -> None:
        agora = agora if agora is not None else time.time()
        self.omega = min(1.0, self.omega + fator)
        self.tau = agora


class MemoriaZ:
    """O mundo onde zbits nascem, vivem e morrem. I5: loga tudo."""

    def __init__(self) -> None:
        self.zbits: dict[str, Zbit] = {}
        self.log: list[tuple] = []

    def nascer(self, v: float, kappa: str, omega0: float,
               lam: float = 0.9) -> Zbit:
        z = Zbit(v=v, kappa=kappa, tau=time.time(), omega=omega0, lam=lam)
        self.zbits[kappa] = z
        self.log.append(("nascimento", kappa, omega0))
        return z

    def reforcar(self, kappa: str, fator: float = 0.1) -> None:
        z = self.zbits.get(kappa)
        if z:
            z.reforcar(fator)
            self.log.append(("reforco", kappa, z.omega))

    def ceifar(self) -> list[str]:
        agora = time.time()
        mortos = [k for k, z in self.zbits.items() if z.morto(agora)]
        for k in mortos:
            del self.zbits[k]
            self.log.append(("morte", k))
        return mortos

    def ler(self, kappa: str) -> Zbit | None:
        return self.zbits.get(kappa)

    def esquecer(self, kappa: str) -> bool:          # I6 · precedente 14h
        if kappa in self.zbits:
            del self.zbits[kappa]
            self.log.append(("morte_por_decreto", kappa))
            return True
        return False