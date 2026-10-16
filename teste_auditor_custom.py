from luma_audit import LUMA, Veredito


def teste_default_backward_compat():
    v = LUMA().auditar({"acao": "ajustar_brilho", "valor": 80},
                       {"lux": 5000, "hora": "14h", "origem": "SENSOR"})
    assert v == Veredito.APROVADA


def teste_custom_limits_aceita():
    a = LUMA(limites={"transferir_mb": (0, 500)})
    v = a.auditar({"acao": "transferir_mb", "valor": 250},
                  {"lux": 5000, "hora": "14h", "origem": "SENSOR"})
    assert v == Veredito.APROVADA


def teste_custom_limits_rejeita_fora_range():
    a = LUMA(limites={"transferir_mb": (0, 500)})
    v = a.auditar({"acao": "transferir_mb", "valor": 9999},
                  {"lux": 5000, "hora": "14h", "origem": "SENSOR"})
    assert v == Veredito.REJEITADA


def teste_custom_sensor():
    a = LUMA(limites={"acao_x": (0, 100)}, sensor="disk_free", sensor_range=(0, 50))
    v = a.auditar({"acao": "acao_x", "valor": 50},
                  {"disk_free": 40, "hora": "14h", "origem": "SENSOR"})
    assert v == Veredito.APROVADA


def teste_custom_sensor_fora_range():
    a = LUMA(limites={"acao_x": (0, 100)}, sensor="disk_free", sensor_range=(0, 50))
    v = a.auditar({"acao": "acao_x", "valor": 50},
                  {"disk_free": 999, "hora": "14h", "origem": "SENSOR"})
    assert v == Veredito.REJEITADA


def teste_custom_teto_declarado():
    a = LUMA(limites={"acao_y": (0, 100)}, teto_declarado=0.10)
    # 85 fora do teto (10,90) -> REJEITADA
    v = a.auditar({"acao": "acao_y", "valor": 85},
                  {"lux": 5000, "hora": "14h", "origem": "DECLARADO"})
    assert v == Veredito.REJEITADA
    # 50 dentro -> APROVADA
    v = a.auditar({"acao": "acao_y", "valor": 50},
                  {"lux": 5000, "hora": "14h", "origem": "DECLARADO"})
    assert v == Veredito.APROVADA
