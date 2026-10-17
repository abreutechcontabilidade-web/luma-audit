"""QubitState - superposicao deterministica de veredictos."""
from __future__ import annotations
import cmath
from dataclasses import dataclass

@dataclass
class QubitState:
    """|psi> = a|aprovada> + b|ajustada> + c|rejeitada>."""
    aprovada: complex = complex(1, 0)
    ajustada: complex = complex(0, 0)
    rejeitada: complex = complex(0, 0)

    def norma(self) -> float:
        return (abs(self.aprovada)**2 + abs(self.ajustada)**2 +
                abs(self.rejeitada)**2)

    def normalizar(self) -> "QubitState":
        n = self.norma()
        if n == 0:
            return QubitState()
        f = 1.0 / cmath.sqrt(n)
        return QubitState(
            aprovada=self.aprovada * f,
            ajustada=self.ajustada * f,
            rejeitada=self.rejeitada * f,
        )

    def colapsar(self) -> str:
        """Projeccao determinista: maior modulo vence."""
        amps = {
            "aprovada": abs(self.aprovada),
            "ajustada": abs(self.ajustada),
            "rejeitada": abs(self.rejeitada),
        }
        return max(amps, key=amps.get)
