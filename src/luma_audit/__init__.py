"""
luma-audit - Governanca deterministica no ponto de execucao.

Camada 0: auditoria de texto/prompt (I0, I1).
Camada 1: auditoria de acao isolada (I1, I3, I4, I5).
Camada 2: auditoria de trajetoria (I4b, I8, I10).
Camada 3: auto-monitorizacao (sentinela + vigia).
"""
from .auditor import LUMA, Veredito
from .prompt_audit import PromptAudit
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

__version__ = "0.5.0"
__all__ = [
    "LUMA", "Veredito", "PromptAudit",
    "Sessao", "AuditorTrajetoria", "VereditoTrajetoria",
    "RISCO_BASE", "JANELA_S", "TETO_RISCO", "TETO_ACOES",
    "CanalUnico", "MensagemFunil",
    "FunilUnico", "FILA_DIR",
    "Sentinela", "Vigia",
]
