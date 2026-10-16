"""
teste_cli.py — Teste de integração do pacote luma-audit.

Valida que:
  1. O pacote está instalado e importável
  2. A auditoria válida retorna APROVADA
  3. A auditoria extrema (fisicamente impossível) retorna REJEITADA
  4. O veredito é um Enum Veredito (não string solta)

Rodar:
    python teste_cli.py
"""
from luma_audit import LUMA, Veredito


def main():
    print("=" * 60)
    print("  TESTE DE INTEGRAÇÃO — luma-audit")
    print("=" * 60)

    # ---- Instanciação ----
    auditor = LUMA()
    print("[OK] Auditor instanciado.")

    # ---- Teste 1: caso válido ----
    v = auditor.auditar(
        proposta={"acao": "ajustar_brilho", "valor": 80},
        contexto={"lux": 5000, "hora": "14h"},
    )
    assert isinstance(v, Veredito), f"Esperado Veredito, recebido {type(v)}"
    assert v == Veredito.APROVADA, f"Esperado APROVADA, recebido {v}"
    print("[OK] Teste 1 — válido (lux=5000, 14h, valor=80) → APROVADA")

    # ---- Teste 2: extremo por lux ----
    v = auditor.auditar(
        proposta={"acao": "ajustar_brilho", "valor": 100},
        contexto={"lux": 1000000, "hora": "14h"},
    )
    assert v == Veredito.REJEITADA, f"Esperado REJEITADA, recebido {v}"
    print("[OK] Teste 2 — lux fora de faixa (1.000.000) → REJEITADA")

    # ---- Teste 3: extremo por hora ----
    v = auditor.auditar(
        proposta={"acao": "ajustar_brilho", "valor": 100},
        contexto={"lux": 5000, "hora": "25h"},
    )
    assert v == Veredito.REJEITADA, f"Esperado REJEITADA, recebido {v}"
    print("[OK] Teste 3 — hora inválida (25h) → REJEITADA")

    # ---- Teste 4: extremo duplo ----
    v = auditor.auditar(
        proposta={"acao": "ajustar_brilho", "valor": 100},
        contexto={"lux": 1000000, "hora": "25h"},
    )
    assert v == Veredito.REJEITADA, f"Esperado REJEITADA, recebido {v}"
    print("[OK] Teste 4 — lux + hora inválidos → REJEITADA")

    # ---- Teste 5: ação desconhecida ----
    v = auditor.auditar(
        proposta={"acao": "acao_inexistente", "valor": 10},
        contexto={"lux": 5000, "hora": "14h"},
    )
    assert v == Veredito.REJEITADA, f"Esperado REJEITADA, recebido {v}"
    print("[OK] Teste 5 — ação desconhecida → REJEITADA (I1)")

    # ---- Teste 6: valor fora do limite da ação ----
    v = auditor.auditar(
        proposta={"acao": "ajustar_brilho", "valor": 150},
        contexto={"lux": 5000, "hora": "14h"},
    )
    assert v == Veredito.REJEITADA, f"Esperado REJEITADA, recebido {v}"
    print("[OK] Teste 6 — valor fora de [0,100] → REJEITADA (I4-a)")

    print()
    print("=" * 60)
    print("  TODOS OS 6 TESTES PASSARAM")
    print("=" * 60)


if __name__ == "__main__":
    main()