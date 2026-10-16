# luma_audit.py - Camada Constitucional da LUMA
# I4: limites fisicos - I6: proveniencia - I7: limite/dominio customizavel
from enum import Enum


class Veredito(Enum):
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"


class LUMA:
    """Auditor determinista de acoes de IA.

    Default: controlo de luz (BH1750).
    Custom: passa limites e sensor no construtor.

    Exemplo generico:
        LUMA(limites={"transferir_mb": (0, 500)},
             sensor="disk_free",
             sensor_range=(0, 100000))
    """

    # Default: controlo de luz
    LIMITES_DEFAULT = {
        "ajustar_gamma":  (0.5, 1.6),
        "ajustar_brilho": (0.0, 100.0),
    }
    LUX_MIN_DEFAULT = 0
    LUX_MAX_DEFAULT = 100000

    ORIGENS = ("SENSOR", "DECLARADO")
    TETO_DECLARADO = 0.25

    def __init__(self, limites=None, sensor="lux",
                 sensor_range=None, teto_declarado=None):
        self.LIMITES = dict(limites) if limites else dict(self.LIMITES_DEFAULT)
        self.SENSOR = sensor
        if sensor_range:
            self.SENSOR_MIN, self.SENSOR_MAX = sensor_range
        else:
            self.SENSOR_MIN = self.LUX_MIN_DEFAULT
            self.SENSOR_MAX = self.LUX_MAX_DEFAULT
        self.TETO_DECLARADO = teto_declarado if teto_declarado is not None else 0.25

    def auditar(self, proposta: dict, contexto: dict) -> Veredito:
        acao = proposta.get("acao")
        if acao not in self.LIMITES:
            return Veredito.REJEITADA

        valor = proposta.get("valor")
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            return Veredito.REJEITADA

        lo, hi = self.LIMITES[acao]

        # I6: origem (default SENSOR)
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

        # I4-b: leitura do sensor
        leitura = contexto.get(self.SENSOR)
        if leitura is None:
            leitura = contexto.get("lux")  # backward-compat
        if not isinstance(leitura, (int, float)) or isinstance(leitura, bool):
            return Veredito.REJEITADA
        if not (self.SENSOR_MIN <= leitura <= self.SENSOR_MAX):
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
