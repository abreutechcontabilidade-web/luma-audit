import tempfile
from pathlib import Path
from luma_audit.swarm import Ledger, SkillPool, Role, Skill


def _tmp():
    return Path(tempfile.mkdtemp()) / "ledger.json"


def teste_ledger_vazio():
    L = Ledger()
    assert L.eventos == []
    assert L.verificar() is True


def teste_ledger_append_e_cadeia():
    L = Ledger()
    L.append("auditar", {"acao": "ajustar_brilho", "valor": 80})
    L.append("auditar", {"acao": "ajustar_brilho", "valor": 50})
    assert len(L.eventos) == 2
    assert L.verificar() is True


def teste_ledger_tampering():
    p = _tmp()
    L = Ledger(p)
    L.append("x", {"v": 1})
    L.append("x", {"v": 2})
    dados = p.read_text(encoding="utf-8")
    dados = dados.replace(chr(34) + "v" + chr(34) + ": 2",
                          chr(34) + "v" + chr(34) + ": 999", 1)
    p.write_text(dados, encoding="utf-8")
    L2 = Ledger(p)
    assert L2.verificar() is False


def teste_pool_default():
    p = SkillPool.default()
    ok, motivo = p.validar("luz", {"skill": "ajustar_brilho", "valor": 80})
    assert ok is True and motivo == "ok"


def teste_pool_rejeita_fora_range_e_desconhecido():
    p = SkillPool.default()
    ok1, _ = p.validar("luz", {"skill": "ajustar_brilho", "valor": 999})
    ok2, _ = p.validar("luz", {"skill": "transferir_mb", "valor": 100})
    ok3, _ = p.validar("hacker", {"skill": "ajustar_brilho", "valor": 50})
    assert ok1 is False
    assert ok2 is False
    assert ok3 is False
