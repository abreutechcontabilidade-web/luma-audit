import hashlib
import tempfile
from pathlib import Path
from luma_audit.swarm import (Ledger, SkillPool, SensorBinding,
                              CommitKernel)


def _k():
    p = Path(tempfile.mkdtemp()) / "led.json"
    L = Ledger(p)
    S = SensorBinding(hashlib.sha256(b"seed-a").digest())
    K = CommitKernel(SkillPool.default(), S, L)
    return K, S, L


def _ctx(S, nome, valor):
    r = S.ler(nome, valor)
    return {"sensor_nome": r.nome, "sensor_valor": r.valor,
            "sensor_ts": r.ts, "sensor_sig": r.assinatura}


def teste_commit_ok():
    K, S, L = _k()
    r = K.commit("luz", {"skill": "ajustar_brilho", "valor": 80},
                 _ctx(S, "bh1750", 5000))
    assert r.ok is True
    assert r.motivo == "ok"
    assert L.verificar() is True


def teste_commit_skill_nao_autorizada():
    K, S, L = _k()
    r = K.commit("luz", {"skill": "transferir_mb", "valor": 100},
                 _ctx(S, "bh1750", 5000))
    assert r.ok is False
    assert "skill_nao_autorizada" in r.motivo


def teste_commit_fora_range():
    K, S, L = _k()
    r = K.commit("luz", {"skill": "ajustar_brilho", "valor": 999},
                 _ctx(S, "bh1750", 5000))
    assert r.ok is False
    assert "fora_limite" in r.motivo


def teste_commit_sensor_ausente():
    K, S, L = _k()
    r = K.commit("luz", {"skill": "ajustar_brilho", "valor": 80}, {})
    assert r.ok is False
    assert r.motivo == "sensor_ausente"


def teste_commit_sensor_inativo():
    K, S, L = _k()
    ctx = _ctx(S, "bh1750", 5000)
    S.marcar_falha("bh1750")
    r = K.commit("luz", {"skill": "ajustar_brilho", "valor": 80}, ctx)
    assert r.ok is False
    assert "sensor_inativo" in r.motivo


def teste_commit_assinatura_invalida():
    K, S, L = _k()
    ctx = _ctx(S, "bh1750", 5000)
    ctx["sensor_sig"] = "0" * 32
    r = K.commit("luz", {"skill": "ajustar_brilho", "valor": 80}, ctx)
    assert r.ok is False
    assert "assinatura_invalida" in r.motivo
