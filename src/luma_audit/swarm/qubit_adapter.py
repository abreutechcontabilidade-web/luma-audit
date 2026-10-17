"""qubit_adapter.py - Usa QubitState para modular o veredicto."""
from __future__ import annotations
from .commit_kernel import CommitKernel, CommitResult
from .qubit import QubitState
from . import gates

class QubitAdapter:
    def __init__(self, kernel: CommitKernel):
        self.kernel = kernel

    def commit_qubit(self, role: str, proposta: dict, contexto: dict,
                     peso_bias: float = 0.0) -> CommitResult:
        # 1. Executa o kernel classico (deterministico)
        res = self.kernel.commit(role, proposta, contexto)

        # 2. Mapeia o resultado para um estado quantico inicial
        if res.ok:
            psi = QubitState(aprovada=complex(1,0))
        else:
            psi = QubitState(rejeitada=complex(1,0))

        # 3. Aplica gates evolutivos (ex: bias para ajustada)
        if peso_bias != 0:
            psi = gates.gate_bias(psi, peso_bias)

        # 4. Colapsa deterministicamente
        veredito_qubit = psi.colapsar()

        # 5. Regista no ledger (via kernel)
        # FIX: converter amplitudes complexas para [real, imag]
        self.kernel.ledger.append("qubit_commit", {
            "role": role, "veredito_qubit": veredito_qubit,
            "amplitudes": {
                "a": [psi.aprovada.real, psi.aprovada.imag],
                "b": [psi.ajustada.real, psi.ajustada.imag],
                "c": [psi.rejeitada.real, psi.rejeitada.imag],
            }
        })

        return CommitResult(res.ok, veredito_qubit, res.evento_hash)
