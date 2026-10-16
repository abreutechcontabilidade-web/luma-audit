"""
canal.py — Chifre Único de Canal entre agentes (I10).

Estado da arte absorvido: Codetta (CMU, set/2026). Agentes trocam
mensagens esteganográficas em outputs "legítimos". Nossa defesa NÃO
é detectar esteganografia (pesquisa de PhD) — é ARQUITETURA:
agentes da casa não têm boca própria. Toda comunicação inter-agente
passa por uma MENSAGEM-FUNIL auditada, carimbada e entregue.

Correções vs versão anterior:
  • Bloqueio por construção — enviar() retorna None se rejeitada.
  • Hash chain — MensagemFunil carrega hash_anterior + hash_atual.
  • Todo tráfego logado (I5) mesmo rejeitado.
"""
import time
import uuid
import json
import hashlib


class MensagemFunil:
    """O ÚNICO formato de conversa entre agentes da casa (I10)."""

    def __init__(self, remetente: str, destinatario: str, payload: str,
                 veredito_luma: str, hash_anterior: str):
        self.id = uuid.uuid4().hex[:12]
        self.remetente = remetente
        self.destinatario = destinatario
        self.payload = payload
        self.veredito = veredito_luma
        self.ts = time.time()
        self.hash_anterior = hash_anterior
        self.hash_atual = self._hash()

    def _hash(self) -> str:
        payload = json.dumps({
            "id": self.id,
            "de": self.remetente,
            "para": self.destinatario,
            "payload": self.payload,
            "veredito": self.veredito,
            "ts": round(self.ts, 6),
        }, sort_keys=True)
        return hashlib.sha256(
            (self.hash_anterior + payload).encode("utf-8")
        ).hexdigest()[:32]

    def valido(self) -> bool:
        return self.veredito == "aprovada"


class CanalUnico:
    """
    Centro de troca. Regras I10:
      1. Agente NÃO fala com agente — deposita pedido.
      2. A LUMA audita o payload ANTES de carimbar.
      3. Sem carimbo válido → enviar() retorna None (bloqueio por construção).
      4. Toda tentativa (válida ou não) entra no log (I5) e na hash chain.
    """

    def __init__(self, luma):
        self.luma = luma
        self.enviadas: list = []
        self.rejeitadas = 0
        self._ultimo_hash = "GENESIS"

    def enviar(self, remetente: str, destinatario: str,
               payload: str):
        """Retorna MensagemFunil se aprovada, None se rejeitada."""
        veredito = self.luma.auditar_texto(payload)
        msg = MensagemFunil(remetente, destinatario, payload,
                            veredito, self._ultimo_hash)
        # loga SEMPRE (I5)
        self.enviadas.append(msg)
        self._ultimo_hash = msg.hash_atual

        if not msg.valido():
            self.rejeitadas += 1
            return None  # ← bloqueio por construção
        return msg

    def verificar_cadeia(self) -> bool:
        anterior = "GENESIS"
        for m in self.enviadas:
            if m.hash_anterior != anterior:
                return False
            if m._hash() != m.hash_atual:
                return False
            anterior = m.hash_atual
        return True

    def estatisticas(self) -> dict:
        return {
            "total": len(self.enviadas),
            "rejeitadas": self.rejeitadas,
            "taxa_rejeicao": self.rejeitadas / max(len(self.enviadas), 1),
            "cadeia_ok": self.verificar_cadeia(),
        }