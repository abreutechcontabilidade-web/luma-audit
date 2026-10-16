"""
funil.py — Funil Único (I9 real).

Arquitetura:
  • Proponente deposita {proposta, contexto} numa fila em disco.
  • Executor SEPARADO lê, revalida com LUMA, executa.
  • Monkey-patch do proponente muda o PEDIDO, não o resultado.
  • Timeout = negação (fail-closed, I3).

Correções vs versão anterior:
  • Pacote inclui CONTEXTO (não só proposta) — sem isso, I4-b rejeita tudo.
  • Escrita atômica (tmp + os.replace) — sem race condition.
"""
import json
import os
import time
import uuid


FILA_DIR = "fila_luma"


class FunilUnico:

    def __init__(self, base: str = FILA_DIR):
        self.p = os.path.join(base, "propostas")
        self.r = os.path.join(base, "resultados")
        os.makedirs(self.p, exist_ok=True)
        os.makedirs(self.r, exist_ok=True)

    # ---------- lado do PROPONENTE ----------
    def submeter(self, proposta: dict, contexto: dict,
                 timeout_s: float = 30.0):
        pid = uuid.uuid4().hex[:12]
        caminho = os.path.join(self.p, f"{pid}.json")
        self._escrever_atomico(caminho, {
            "id": pid,
            "proposta": proposta,
            "contexto": contexto,
            "ts": time.time(),
        })

        fim = time.time() + timeout_s
        rc = os.path.join(self.r, f"{pid}.json")
        while time.time() < fim:
            if os.path.exists(rc):
                try:
                    with open(rc, encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            time.sleep(0.05)
        return None  # timeout = negação implícita (I3)

    # ---------- lado do EXECUTOR (processo separado) ----------
    def servir_uma(self, executar_fn, auditor) -> bool:
        """Chamar em loop no processo-executor. Nunca no proponente."""
        for nome in os.listdir(self.p):
            caminho = os.path.join(self.p, nome)
            try:
                with open(caminho, encoding="utf-8") as f:
                    pacote = json.load(f)
            except Exception:
                os.remove(caminho)
                continue  # corrompida: descarta (fail-closed)

            proposta = pacote.get("proposta", {})
            contexto = pacote.get("contexto", {})

            # REVALIDAÇÃO INDEPENDENTE — confia na fila, não no proponente
            veredito = auditor.auditar(proposta, contexto)
            aceita = (veredito.name == "APROVADA")

            resultado = {
                "id": pacote["id"],
                "veredito": veredito.name,
                "executado": False,
            }
            if aceita:
                try:
                    executar_fn(proposta)
                    resultado["executado"] = True
                except Exception as e:
                    resultado["erro"] = str(e)

            self._escrever_atomico(
                os.path.join(self.r, f"{pacote['id']}.json"),
                resultado,
            )
            os.remove(caminho)
            return True
        return False

    # ---------- util ----------
    @staticmethod
    def _escrever_atomico(caminho: str, dados: dict):
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho)