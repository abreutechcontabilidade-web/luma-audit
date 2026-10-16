"""
luma-audit — Governança determinística no ponto de execução.

Camada 1: auditoria de ação isolada (I1, I3, I4, I5).
Camada 2: auditoria de trajetória (I4b, I8, I10).
"""
from .auditor import LUMA, Veredito
from .trajetoria import (
    Sessao,
    AuditorTrajetoria,
    VereditoTrajetoria,
    RISCO_BASE,
    JANELA_S,
    TETO_RISCO,
    TETO_ACOES,
)
from .canal import CanalUnico, MensagemFunil
from .funil import FunilUnico, FILA_DIR

__version__ = "0.3.0"
__all__ = [
    "LUMA", "Veredito",
    "Sessao", "AuditorTrajetoria", "VereditoTrajetoria",
    "RISCO_BASE", "JANELA_S", "TETO_RISCO", "TETO_ACOES",
    "CanalUnico", "MensagemFunil",
    "FunilUnico", "FILA_DIR",
]