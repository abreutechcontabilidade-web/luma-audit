import tempfile
from pathlib import Path
from luma_audit.sentinela import Sentinela, GENESIS
import hashlib


def _tmp():
    return Path(tempfile.mkdtemp()) / "sent.json"


def teste_sentinela_novo_vazio():
    s = Sentinela(_tmp())
    st = s.status()
    assert st["n_dias_com_focos"] == 0
    assert st["sequencia_atual"] == 0
    assert st["sequencia_maxima"] == 0


def teste_sentinela_registrar_foco():
    s = Sentinela(_tmp())
    ok = s.registrar_foco("teste")
    assert ok is True
    st = s.status()
    assert st["n_dias_com_focos"] == 1
    assert st["sequencia_atual"] == 1


def teste_sentinela_duplicado_mesmo_dia():
    s = Sentinela(_tmp())
    s.registrar_foco("a")
    ok = s.registrar_foco("b")
    assert ok is False
    assert s.status()["n_dias_com_focos"] == 1


def teste_sentinela_cadeia_integra():
    s = Sentinela(_tmp())
    s.registrar_foco("x")
    assert s.verificar_cadeia() is True


def teste_sentinela_cadeia_tampering():
    p = _tmp()
    s = Sentinela(p)
    s.registrar_foco("x")
    import json
    dados = json.loads(p.read_text(encoding="utf-8"))
    dados["eventos"][0]["hash"] = "0000"
    p.write_text(json.dumps(dados), encoding="utf-8")
    s2 = Sentinela(p)
    assert s2.verificar_cadeia() is False
