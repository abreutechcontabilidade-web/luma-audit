# luma_audit.py — Camada Constitucional da LUMA (auditor deterministico)
# I1: funil unico · I3: fail-closed · I4: limites fisicos + plausibilidade
# I5: quem loga e o zbit
from enum import Enum


class Veredito(Enum):
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"


class LUMA:
    # I4: limites fisicos declarados por acao
    LIMITES = {
        "ajustar_gamma":  (0.5, 1.6),
        "ajustar_brilho": (0.0, 100.0),
    }

    # Limites plausiveis do sensor BH1750
    LUX_MIN = 0
    LUX_MAX = 100000

    def auditar(self, proposta: dict, contexto: dict) -> Veredito:
        # I1: so acoes conhecidas passam
        acao = proposta.get("acao")
        if acao not in self.LIMITES:
            return Veredito.REJEITADA

        # tipo do valor
        valor = proposta.get("valor")
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            return Veredito.REJEITADA

        # I4-a: valor dentro dos limites fisicos da acao
        lo, hi = self.LIMITES[acao]
        if not (lo <= valor <= hi):
            return Veredito.REJEITADA

        # I4-b: contexto do sensor tem que ser fisicamente plausivel
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