from luma_audit import LUMA, Veredito


def _a(): return LUMA()


def teste_sem_origem_default_sensor():
    # 80 dentro de (0,100) - sem origem assume SENSOR - APROVADA
    v = _a().auditar({"acao": "ajustar_brilho", "valor": 80}, {"lux": 5000, "hora": "14h"})
    assert v == Veredito.APROVADA


def teste_declarado_dentro_teto():
    # 50 dentro do teto (25,75) - APROVADA
    v = _a().auditar({"acao": "ajustar_brilho", "valor": 50},
                     {"lux": 5000, "hora": "14h", "origem": "DECLARADO"})
    assert v == Veredito.APROVADA


def teste_declarado_fora_teto():
    # 80 fora do teto (25,75) - REJEITADA
    v = _a().auditar({"acao": "ajustar_brilho", "valor": 80},
                     {"lux": 5000, "hora": "14h", "origem": "DECLARADO"})
    assert v == Veredito.REJEITADA


def teste_sensor_range_completo():
    v = _a().auditar({"acao": "ajustar_brilho", "valor": 100},
                     {"lux": 5000, "hora": "14h", "origem": "SENSOR"})
    assert v == Veredito.APROVADA


def teste_origem_invalida():
    v = _a().auditar({"acao": "ajustar_brilho", "valor": 50},
                     {"lux": 5000, "hora": "14h", "origem": "HACKER"})
    assert v == Veredito.REJEITADA


def teste_gamma_declarado_fora_teto():
    # range (0.5,1.6), teto DECLARADO (0.775, 1.325); 1.5 > 1.325 -> REJEITADA
    v = _a().auditar({"acao": "ajustar_gamma", "valor": 1.5},
                     {"lux": 5000, "hora": "14h", "origem": "DECLARADO"})
    assert v == Veredito.REJEITADA
