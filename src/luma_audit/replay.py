"""replay.py - verificacao publica do ledger (L6).

Um terceiro com o ficheiro do ledger recomputa todos os hashes.
Se bater, prova integridade. Se nao, tampering.
"""
from __future__ import annotations

from pathlib import Path

from .swarm.ledger import Ledger


def verificar_ledger(caminho: Path | str) -> dict:
    L = Ledger(caminho)
    integro = L.verificar()
    return {
        "n_eventos": len(L.eventos),
        "integro": integro,
        "head": L.head,
        "primeiro_ts": L.eventos[0].ts if L.eventos else None,
        "ultimo_ts": L.eventos[-1].ts if L.eventos else None,
    }
