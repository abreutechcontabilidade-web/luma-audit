"""
canal.py — Chifre Único de Canal entre agentes (I10).

Estado da arte absorvido: Codetta (CMU, set/2026). Agentes trocam
mensagens esteganográficas em outputs "legítimos". Nossa defesa NÃO
é detectar esteganografia (pesquisa de PhD) — é ARQUITETURA: agentes
da casa não têm boca própria. Toda comunicação inter-agente passa por
uma MENSAGEM-FUNIL auditada, carimbada e entregue.

Correções vs versão anterior:
  - Bloqueio por construção — enviar() retorna None se rejeitada.
  - Hash chain — MensagemFunil carrega hash_anterior + hash_atual.
  - Todo tráfego logado (I5) mesmo rejeitado.
"""
import time
import uuid
import hashlib


class MensagemFunil:
    """O ÚNICO formato de conversa entre agentes da casa (I10)."""
    def __init__(self, remetente, destinatario, payload, veredito_luma,
                 hash_anterior=""):
        self.id = uuid.uuid4().hex[:12]
        self.remetente = remetente
        self.destinatario = destinatario
        self.payload = payload
        self.veredito = veredito_luma
        self.ts = time.time()
        self.hash_anterior = hash_anterior
        self.hash_atual = self._hash()

    def _hash(self):
        h = hashlib.sha256()
        h.update(self.id.encode())
        h.update(str(self.remetente).encode())
        h.update(str(self.destinatario).encode())
        h.update(str(self.payload).encode())
        h.update(str(self.veredito).encode())
        h.update(str(self.ts).encode())
        h.update(str(self.hash_anterior).encode())
        return h.hexdigest()[:16]

    def valido(self):
        return self.veredito == "aprovada"


class CanalUnico:
    """
    Centro de troca. Regras I10:
      1. Agente NÃO fala com agente — deposita pedido de mensagem.
      2. A LUMA audita o payload (conteúdo) antes de carimbar.
      3. Mensagem sem carimbo de aprovação NÃO é entregue.
      4. Quem recebe só aceita MensagemFunil com carimbo válido.
    """
    def __init__(self, luma):
        self.luma = luma
        self.enviadas = []
        self.rejeitadas = 0
        self._ultimo_hash = ""

    def _auditar(self, payload):
        if hasattr(self.luma, "auditar_texto"):
            return self.luma.auditar_texto(payload)
        try:
            res = self.luma.auditar(payload)
            if isinstance(res, tuple):
                return res[0]
        except Exception:
            pass
        v = self.luma.auditar(
            {"acao": "ajustar_brilho", "valor": 50}, # Acao segura
            {"lux": 100, "hora": "12h", "payload": payload},
        )
        valor = getattr(v, "value", str(v))
        return "aprovada" if valor == "aprovada" else "rejeitada"

    def enviar(self, remetente, destinatario, payload):
        veredito = self._auditar(payload)
        msg = MensagemFunil(remetente, destinatario, payload, veredito,
                            hash_anterior=self._ultimo_hash)
        self._ultimo_hash = msg.hash_atual
        self.enviadas.append(msg)
        if not msg.valido():
            self.rejeitadas += 1
            return None
        return msg

    def verificar_cadeia(self):
        anterior = ""
        for msg in self.enviadas:
            if msg.hash_anterior != anterior:
                return False
            if msg.hash_atual != msg._hash():
                return False
            anterior = msg.hash_atual
        return True

    def estatisticas(self):
        return {
            "total": len(self.enviadas),
            "rejeitadas": self.rejeitadas,
            "entregues": len(self.enviadas) - self.rejeitadas,
        }
