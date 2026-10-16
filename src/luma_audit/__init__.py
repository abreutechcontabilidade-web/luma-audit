"""
luma-audit - Governanca deterministica no ponto de execucao.

Camada 1: auditoria de acao isolada (I1, I3, I4, I5).
Camada 2: auditoria de trajetoria (I4b, I8, I10).
Camada 3: auto-monitorizacao (sentinela + vigia).
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
from .sentinela import Sentinela
from .vigia import Vigia

__version__ = "0.4.0"
__all__ = [
    "LUMA", "Veredito",
    "Sessao", "AuditorTrajetoria", "VereditoTrajetoria",
    "RISCO_BASE", "JANELA_S", "TETO_RISCO", "TETO_ACOES",
    "CanalUnico", "MensagemFunil",
    "FunilUnico", "FILA_DIR",
    "Sentinela", "Vigia",
]
