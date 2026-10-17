"""gates.py - Operadores unitarios sobre QubitState."""
from __future__ import annotations
import cmath
from .qubit import QubitState

def gate_hadamard(q: QubitState) -> QubitState:
    """H generalizada: cria superposicao entre aprovada e rejeitada."""
    f = 1.0 / cmath.sqrt(2)
    return QubitState(
        aprovada=(q.aprovada + q.rejeitada) * f,
        ajustada=q.ajustada,
        rejeitada=(q.aprovada - q.rejeitada) * f,
    ).normalizar()

def gate_phase(q: QubitState, angulo: float) -> QubitState:
    """Roda a fase da componente ajustada."""
    rot = cmath.exp(1j * angulo)
    return QubitState(
        aprovada=q.aprovada,
        ajustada=q.ajustada * rot,
        rejeitada=q.rejeitada,
    ).normalizar()

def gate_bias(q: QubitState, peso: float) -> QubitState:
    """Inclina o estado para aprovada ou rejeitada (peso entre -1 e 1)."""
    return QubitState(
        aprovada=q.aprovada * (1 + peso),
        ajustada=q.ajustada,
        rejeitada=q.rejeitada * (1 - peso),
    ).normalizar()
