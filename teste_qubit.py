import hashlib
import tempfile
from pathlib import Path
from luma_audit.swarm import (SkillPool, SensorBinding, CommitKernel,
                              Ledger, QubitState, QubitAdapter)
from luma_audit.swarm import gates

def teste_qubit_normalizacao():
    q = QubitState(aprovada=complex(3,0), ajustada=complex(4,0))
    qn = q.normalizar()
    assert abs(qn.norma() - 1.0) < 1e-9

def teste_qubit_colapso():
    q = QubitState(aprovada=complex(0,0), rejeitada=complex(1,0))
    assert q.colapsar() == "rejeitada"

def teste_gate_hadamard():
    q = QubitState(aprovada=complex(1,0))
    qh = gates.gate_hadamard(q)
    assert abs(abs(qh.aprovada) - abs(qh.rejeitada)) < 1e-9

def teste_gate_bias_aprova():
    q = QubitState(aprovada=complex(1,0))
    qb = gates.gate_bias(q, peso=0.5)
    assert qb.colapsar() == "aprovada"

def teste_qubit_adapter():
    p = Path(tempfile.mkdtemp()) / "led.json"
    pool = SkillPool.for_tenant("teste")
    chave = hashlib.sha256(b"seed").digest()
    sensors = SensorBinding(chave)
    led = Ledger(p)
    kernel = CommitKernel(pool, sensors, led)
    adp = QubitAdapter(kernel)
    r = sensors.ler("bh1750", 5000)
    ctx = {"sensor_nome": r.nome, "sensor_valor": r.valor,
           "sensor_ts": r.ts, "sensor_sig": r.assinatura}
    res = adp.commit_qubit("luz", {"skill": "ajustar_brilho", "valor": 80}, ctx)
    assert res.ok is True
    assert led.verificar() is True
