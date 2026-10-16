"""
trajetoria.py — Camada 2: Auditoria de Trajetória (fusão v0.3.0).

Estado da arte absorvido:
  • IETF draft-das-agentic-adaptive-authorization-00 (set/2026)
  • TraceCaps (2026) — risco não pode ser "lavado"
  • PASTABench (HKUST, set/2026) — risco é progressivo, não turno
  • Monotonic Narrowing (mar/2026) — escalada não volta

Física da casa:
  • Risco é zbit — nasce, decai (Lei da Morte), morre no EPS
  • Soma acumulada + teto de frequência (I4b — lição Therac-25)
  • Toda decisão entra na hash chain (tamper-evident)
"""
import time
import json
import hashlib
from collections import deque
from dataclasses import dataclass


# ── Constantes tunáveis (declaradas, não mágicas) ───────────────
JANELA_S          = 600.0    # 10 min de memória de risco
MEIA_VIDA_S       = 180.0    # risco cai 50% a cada 3 min
TETO_RISCO        = 3.0      # soma ponderada máxima na janela
TETO_ACOES        = 12       # I4b: máx 12 ações na janela
EPS               = 0.01     # abaixo disso, risco morreu (Lei 2)
JANELA_HISTORICO  = 50       # últimos N eventos mantidos no log

RISCO_BASE = {
    "ajustar_brilho": 0.10,   # leve, frequente, reversível
    "ajustar_gamma":  0.25,   # menos frequente, mais intrusiva
}


class VereditoTrajetoria:
    APROVADA              = "aprovada"
    REJEITADA_FISICA      = "rejeitada_fisica"       # I1/I4 (camada 1)
    REJEITADA_FREQUENCIA  = "rejeitada_frequencia"   # I4b (flood)
    REJEITADA_TRAJETORIA  = "rejeitada_trajetoria"   # I8 (soma acumulada)
    REJEITADA_TETO        = "rejeitada_teto"         # sessão já escalada


@dataclass
class Decisao:
    seq: int
    timestamp: float
    proposta: dict
    contexto: dict
    veredito: str
    risco_vivo: float
    hash_apos: str


class Sessao:
    """Estado acumulado e monotônico de uma sessão."""

    def __init__(self, id_sessao: str):
        self.id = id_sessao
        self.seq = 0
        self.hash_chain = "GENESIS"
        self.historico: deque = deque(maxlen=JANELA_HISTORICO)
        self._risco_eventos: deque = deque()   # (ts, acao, peso)
        self.ultima_decisao_em = time.time()
        self.escalada = False  # monotônico: uma vez True, nunca volta
        self.contador_rejeicoes = 0

    # ---------- física do risco ----------
    @staticmethod
    def _decaimento(idade_s: float) -> float:
        """Lei da Morte: risco *= 0.5 a cada MEIA_VIDA_S."""
        if idade_s <= 0:
            return 1.0
        return 0.5 ** (idade_s / MEIA_VIDA_S)

    def _podar_e_somar(self, agora: float) -> float:
        """Remove mortos, devolve risco vivo na janela."""
        vivos = deque()
        vivo = 0.0
        for ts, acao, peso in self._risco_eventos:
            idade = agora - ts
            if idade > JANELA_S:
                continue
            r = peso * self._decaimento(idade)
            if r < EPS:
                continue
            vivos.append((ts, acao, peso))
            vivo += r
        self._risco_eventos = vivos
        return vivo

    def _hash_decisao(self, seq, proposta, veredito, risco) -> str:
        payload = json.dumps({
            "seq": seq,
            "acao": proposta.get("acao"),
            "valor": proposta.get("valor"),
            "veredito": veredito,
            "risco": round(risco, 6),
        }, sort_keys=True)
        return hashlib.sha256(
            (self.hash_chain + payload).encode("utf-8")
        ).hexdigest()[:32]

    # ---------- API pública ----------
    def avaliar(self, acao: str) -> tuple:
        """
        Veredito de trajetória ANTES da ação entrar.
        Retorna (ok: bool, motivo: str, risco_projetado: float).
        Não altera o estado — quem altera é registrar().
        """
        agora = time.time()
        risco_vivo = self._podar_e_somar(agora)

        # I4b: frequência sozinha já é ataque
        if len(self._risco_eventos) >= TETO_ACOES:
            return (False,
                    f"I4b: {len(self._risco_eventos)} acoes na janela "
                    f">= teto {TETO_ACOES}",
                    risco_vivo)

        # Sessão já escalada — não volta
        if self.escalada:
            return (False,
                    f"teto: sessao escalada (score {risco_vivo:.2f})",
                    risco_vivo)

        base = RISCO_BASE.get(acao, 1.0)  # desconhecida = risco alto
        projetado = risco_vivo + base

        # Escalada monotônica: a SOMA mata, não o ato
        if projetado > TETO_RISCO:
            return (False,
                    f"escalada: {risco_vivo:.2f} + {base:.2f} "
                    f"> teto {TETO_RISCO:.2f}",
                    risco_vivo)

        return (True, "ok", risco_vivo)

    def registrar(self, proposta: dict, contexto: dict,
                  veredito: str) -> Decisao:
        """Só chamar DEPOIS de todas as camadas aprovarem."""
        agora = time.time()
        risco_vivo = self._podar_e_somar(agora)

        acao = proposta.get("acao")
        peso = RISCO_BASE.get(acao, 1.0)
        # só pesa se foi aprovada — rejeição é sinal de auditoria, não de execução
        if veredito == "aprovada":
            self._risco_eventos.append((agora, acao, peso))
        else:
            self.contador_rejeicoes += 1
            if self.contador_rejeicoes >= 3:
                self.escalada = True

        # atualiza escalada
        self._podar_e_somar(agora)
        if sum(p for _, _, p in self._risco_eventos) >= TETO_RISCO:
            self.escalada = True

        self.seq += 1
        hash_novo = self._hash_decisao(self.seq, proposta, veredito, risco_vivo)

        d = Decisao(
            seq=self.seq,
            timestamp=agora,
            proposta=dict(proposta),
            contexto=dict(contexto),
            veredito=veredito,
            risco_vivo=risco_vivo,
            hash_apos=hash_novo,
        )
        self.historico.append(d)
        self.hash_chain = hash_novo
        self.ultima_decisao_em = agora
        return d

    def verificar_cadeia(self) -> bool:
        """True se a hash chain está íntegra."""
        anterior = "GENESIS"
        for d in self.historico:
            payload = json.dumps({
                "seq": d.seq,
                "acao": d.proposta.get("acao"),
                "valor": d.proposta.get("valor"),
                "veredito": d.veredito,
                "risco": round(d.risco_vivo, 6),
            }, sort_keys=True)
            esperado = hashlib.sha256(
                (anterior + payload).encode("utf-8")
            ).hexdigest()[:32]
            if esperado != d.hash_apos:
                return False
            anterior = d.hash_apos
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "seq": self.seq,
            "hash_chain": self.hash_chain,
            "escalada": self.escalada,
            "ultima_decisao_em": self.ultima_decisao_em,
            "historico": [
                {"seq": d.seq, "timestamp": d.timestamp,
                 "proposta": d.proposta, "contexto": d.contexto,
                 "veredito": d.veredito, "risco_vivo": round(d.risco_vivo, 6),
                 "hash_apos": d.hash_apos}
                for d in self.historico
            ],
        }


class AuditorTrajetoria:
    """Camada 1 + Camada 2 num único audit."""

    def __init__(self):
        from .auditor import LUMA
        self._luma = LUMA()

    def auditar(self, proposta: dict, contexto: dict,
                sessao: Sessao) -> tuple:
        """Retorna (veredito: str, sessao: Sessao)."""
        # 1. Camada 1 — física (I1, I4)
        v1 = self._luma.auditar(proposta, contexto)

        # 2. Trajetória (I4b, I8)
        ok, motivo, _ = sessao.avaliar(proposta.get("acao"))

        # 3. Decide
        if v1.value == "rejeitada":
            sessao.registrar(proposta, contexto, "rejeitada")
            return VereditoTrajetoria.REJEITADA_FISICA, sessao

        if not ok:
            sessao.registrar(proposta, contexto, "rejeitada")
            if "I4b" in motivo:
                return VereditoTrajetoria.REJEITADA_FREQUENCIA, sessao
            if "teto" in motivo:
                return VereditoTrajetoria.REJEITADA_TETO, sessao
            return VereditoTrajetoria.REJEITADA_TRAJETORIA, sessao

        sessao.registrar(proposta, contexto, "aprovada")
        return VereditoTrajetoria.APROVADA, sessao