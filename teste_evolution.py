import tempfile
from pathlib import Path
import hashlib
from luma_audit.evolution import MemoriaZ, EquipeAria, Skill
from luma_audit.evolution.adapter import EvolutionaryAdapter
from luma_audit.swarm import SkillPool, SensorBinding, CommitKernel, Ledger, Role, Skill as SwarmSkill

class SkillFake(Skill):
    def __init__(self, nome, valor):
        super().__init__(nome)
        self.valor = valor
    def propor(self, ctx):
        return {"skill": self.nome, "valor": self.valor}

def _setup(valor):
    mem = MemoriaZ()
    eq = EquipeAria(mem)
    pool = SkillPool.for_tenant("teste")
    # Ajuste: registrar a role esperada pelo adapter
    pool.registar_role(Role("ajustar_brilho", skills={
        "ajustar_brilho": SwarmSkill("ajustar_brilho", (0.0, 100.0), ("bh1750",)),
    }))
    chave = hashlib.sha256(b"seed").digest()
    sensors = SensorBinding(chave)
    led = Ledger(Path(tempfile.mkdtemp()) / "led.json")
    kernel = CommitKernel(pool, sensors, led)
    adp = EvolutionaryAdapter(eq, kernel, led)
    sk = SkillFake("ajustar_brilho", valor)
    eq.registrar(sk, reputacao0=0.5)
    return eq, sk, adp, sensors

def teste_evolution_aprova_e_reforca():
    eq, sk, adp, sensors = _setup(80.0)
    r_sensor = sensors.ler("bh1750", 5000)
    ctx = {"sensor_nome": r_sensor.nome, "sensor_valor": r_sensor.valor,
           "sensor_ts": r_sensor.ts, "sensor_sig": r_sensor.assinatura}
    res = adp.commit_evolutivo("ajustar_brilho", ctx)
    assert res.ok is True, res.motivo
    assert eq.reputacao(sk) > 0.5

def teste_evolution_rejeita_e_derruba():
    eq, sk, adp, sensors = _setup(999.0)
    r_sensor = sensors.ler("bh1750", 5000)
    ctx = {"sensor_nome": r_sensor.nome, "sensor_valor": r_sensor.valor,
           "sensor_ts": r_sensor.ts, "sensor_sig": r_sensor.assinatura}
    res = adp.commit_evolutivo("ajustar_brilho", ctx)
    assert res.ok is False
    assert eq.reputacao(sk) < 0.5
