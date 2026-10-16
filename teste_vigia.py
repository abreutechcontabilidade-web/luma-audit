from luma_audit.vigia import Vigia, _disco, _memoria, _pasta


def teste_vigia_disco():
    d = _disco(".")
    assert "total_gb" in d
    assert "livre_gb" in d
    assert "uso_pct" in d


def teste_vigia_memoria():
    m = _memoria()
    assert "total_gb" in m
    assert "uso_pct" in m


def teste_vigia_checar_completo():
    v = Vigia(pasta=".")
    r = v.checar()
    assert "disco" in r
    assert "memoria" in r
    assert "pasta" in r
    assert "alertas" in r
    assert isinstance(r["alertas"], list)
