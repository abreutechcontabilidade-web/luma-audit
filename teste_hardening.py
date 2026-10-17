import hashlib, tempfile
from pathlib import Path
import pytest
from luma_audit.swarm import (Ledger, SkillPool, SensorBinding,
                              CommitKernel)


def teste_A2_chave_fraca_recusada():
    with pytest.raises(ValueError, match="chave fraca"):
        SensorBinding(b"chave")


def teste_A2_chave_forte_aceita():
    chave = hashlib.sha256(b"seed-forte").digest()
    s = SensorBinding(chave)
    assert len(s.chave) == 32


def teste_A3_scope_obrigatorio():
    with pytest.raises(ValueError):
        SkillPool(scope="")


def teste_A3_for_tenant_isolado():
    p1 = SkillPool.for_tenant("cliente-A")
    p2 = SkillPool.for_tenant("cliente-B")
    assert p1.scope == "cliente-A"
    assert p2.scope == "cliente-B"
    ok, motivo = p1.validar("luz", {"skill": "ajustar_brilho", "valor": 50})
    assert ok is True
    # motivo incluiria o scope se falhasse


def teste_A4_head_assinada_bate():
    p = Path(tempfile.mkdtemp()) / "led.json"
    L = Ledger(p)
    L.append("x", {"v": 1})
    L.append("y", {"v": 2})
    head = L.eventos[-1].hash
    # recarregar com head externa
    L2 = Ledger(p, head_assinada=head)
    assert L2.verificar() is True


def teste_A4_head_assinada_diferente_recusa():
    p = Path(tempfile.mkdtemp()) / "led.json"
    L = Ledger(p)
    L.append("x", {"v": 1})
    with pytest.raises(ValueError, match="head externo"):
        Ledger(p, head_assinada="0" * 32)
