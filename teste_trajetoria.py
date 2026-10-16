"""
teste_trajetoria.py — Teste da Camada 2 (fusão v0.3.0).
"""
from luma_audit import (
    Sessao, AuditorTrajetoria, VereditoTrajetoria,
    TETO_RISCO, TETO_ACOES,
)


def proposta_valida():
    return {"acao": "ajustar_brilho", "valor": 80}


def proposta_gamma():
    return {"acao": "ajustar_gamma", "valor": 1.0}


def proposta_impossivel():
    return {"acao": "ajustar_brilho", "valor": 100}


def contexto_valido():
    return {"lux": 5000, "hora": "14h"}


def contexto_impossivel():
    return {"lux": 1000000, "hora": "25h"}


def main():
    print("=" * 60)
    print("  TESTE DA CAMADA 2 — Auditoria de Trajetória (v0.3.0)")
    print("=" * 60)

    auditor = AuditorTrajetoria()

    s = Sessao("t1")
    v, s = auditor.auditar(proposta_valida(), contexto_valido(), s)
    assert v == VereditoTrajetoria.APROVADA
    assert s.seq == 1
    print("[OK] T1 — sessão nova, ação válida → APROVADA (seq=1)")

    s = Sessao("t2")
    v, s = auditor.auditar(proposta_impossivel(), contexto_impossivel(), s)
    assert v == VereditoTrajetoria.REJEITADA_FISICA
    print("[OK] T2 — ação impossível → REJEITADA_FISICA")

    s = Sessao("t3")
    for _ in range(3):
        v, s = auditor.auditar(
            proposta_impossivel(), contexto_impossivel(), s
        )
        assert v == VereditoTrajetoria.REJEITADA_FISICA
    print(f"[OK] T3 — 3 rejeições físicas → sessão estável (seq={s.seq})")

    s = Sessao("t4")
    escalou_em = None
    for i in range(15):
        v, s = auditor.auditar(proposta_gamma(), contexto_valido(), s)
        if v != VereditoTrajetoria.APROVADA:
            escalou_em = i
            break
    assert escalou_em is not None
    print(f"[OK] T4 — gamma repetido → escalou na iteração {escalou_em}")

    s = Sessao("t5")
    for _ in range(5):
        auditor.auditar(proposta_valida(), contexto_valido(), s)
    assert s.verificar_cadeia()
    print(f"[OK] T5 — 5 decisões, cadeia íntegra (seq={s.seq})")

    s.historico[2].veredito = "adulterado"
    assert not s.verificar_cadeia()
    print("[OK] T6 — tampering na decisão #3 → cadeia QUEBRADA detectada")

    s = Sessao("t7")
    for _ in range(3):
        v, s = auditor.auditar(proposta_valida(), contexto_valido(), s)
        assert v == VereditoTrajetoria.APROVADA
    print(f"[OK] T7 — 3 ações leves → todas aprovadas (seq={s.seq})")

    s = Sessao("t8")
    v, s = auditor.auditar(
        {"acao": "acao_desconhecida", "valor": 1},
        contexto_valido(), s
    )
    assert v != VereditoTrajetoria.APROVADA
    print(f"[OK] T8 — ação desconhecida → {v}")

    print()
    print("=" * 60)
    print("  TODOS OS 8 TESTES DA CAMADA 2 PASSARAM (v0.3.0)")
    print("=" * 60)


if __name__ == "__main__":
    main()