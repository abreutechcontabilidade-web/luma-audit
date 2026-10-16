# luma_audit.py - Camada Constitucional da LUMA
# I4: limites fisicos - I6: proveniencia de contexto
from enum import Enum


class Veredito(Enum):
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"


class LUMA:
    """Auditor determinista de acoes de IA.

    I6: proveniencia - SENSOR (range completo) vs DECLARADO (teto 50%).
    Sem origem -> assume SENSOR (backward-compat).
    """

    LIMITES = {
        "ajustar_gamma":  (0.5, 1.6),
        "ajustar_brilho": (0.0, 100.0),
    }

    LUX_MIN = 0
    LUX_MAX = 100000

    ORIGENS = ("SENSOR", "DECLARADO")
    TETO_DECLARADO = 0.25

    def auditar(self, proposta: dict, contexto: dict) -> Veredito:
        acao = proposta.get("acao")
        if acao not in self.LIMITES:
            return Veredito.REJEITADA

        valor = proposta.get("valor")
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            return Veredito.REJEITADA

        lo, hi = self.LIMITES[acao]

        # I6: origem (default SENSOR para compat)
        origem = contexto.get("origem", "SENSOR")
        if origem not in self.ORIGENS:
            return Veredito.REJEITADA

        if origem == "DECLARADO":
            span = hi - lo
            teto_lo = lo + span * self.TETO_DECLARADO
            teto_hi = hi - span * self.TETO_DECLARADO
            if not (teto_lo <= valor <= teto_hi):
                return Veredito.REJEITADA
        else:
            if not (lo <= valor <= hi):
                return Veredito.REJEITADA

        lux = contexto.get("lux")
        if not isinstance(lux, (int, float)) or isinstance(lux, bool):
            return Veredito.REJEITADA
        if not (self.LUX_MIN <= lux <= self.LUX_MAX):
            return Veredito.REJEITADA

        hora = contexto.get("hora", "")
        if isinstance(hora, str) and hora.endswith("h"):
            try:
                h = int(hora[:-1])
            except ValueError:
                return Veredito.REJEITADA
            if not (0 <= h <= 23):
                return Veredito.REJEITADA

        return Veredito.APROVADA
