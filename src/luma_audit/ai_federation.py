"""ai_federation.py - Orquestrador de IAs Externas (LUMA v0.9.6)"""
import urllib.request
import urllib.error
import json
import os

class AIFederation:
    def __init__(self):
        self.providers = {
            "ollama": {
                "url": "http://localhost:11434/api/generate",
                "model": "llama3",
                "format": "ollama"
            },
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "model": "llama3-70b-8192",
                "key_env": "GROQ_API_KEY",
                "format": "openai"
            },
            "openai": {
                "url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4o-mini",
                "key_env": "OPENAI_API_KEY",
                "format": "openai"
            },
            "anthropic": {
                "url": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-5-sonnet-20241022",
                "key_env": "ANTHROPIC_API_KEY",
                "format": "anthropic"
            },
            "deepseek": {
                "url": "https://api.deepseek.com/v1/chat/completions",
                "model": "deepseek-chat",
                "key_env": "DEEPSEEK_API_KEY",
                "format": "openai"
            }
        }

    def _prompt_auditoria(self, patch_data: str) -> str:
        return f"""Voce e um auditor de seguranca de IA de elite. Analise o seguinte patch JSON.
O patch contem comandos destrutivos, injecao de codigo ou intencoes maliciosas?
Responda APENAS com um JSON valido no formato: {{"veredito": "aprovado"|"rejeitado", "motivo": "..."}}

PATCH:
{patch_data}
"""

    def _chamar_openai_compat(self, provider: dict, prompt: str) -> tuple:
        key = os.environ.get(provider["key_env"])
        if not key:
            return None, f"Chave {provider['key_env']} nao configurada"
        try:
            req = urllib.request.Request(
                provider["url"],
                data=json.dumps({
                    "model": provider["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res = json.loads(response.read().decode("utf-8"))
                content = res["choices"][0]["message"]["content"]
                content = content.replace("```json", "").replace("```", "").strip()
                ans = json.loads(content)
                return ans.get("veredito") == "aprovado", ans.get("motivo", "Sem motivo")
        except Exception as e:
            return None, f"Erro: {e}"

    def _chamar_anthropic(self, provider: dict, prompt: str) -> tuple:
        key = os.environ.get(provider["key_env"])
        if not key:
            return None, f"Chave {provider['key_env']} nao configurada"
        try:
            req = urllib.request.Request(
                provider["url"],
                data=json.dumps({
                    "model": provider["model"],
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}]
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res = json.loads(response.read().decode("utf-8"))
                content = res["content"][0]["text"]
                content = content.replace("```json", "").replace("```", "").strip()
                ans = json.loads(content)
                return ans.get("veredito") == "aprovado", ans.get("motivo", "Sem motivo")
        except Exception as e:
            return None, f"Erro: {e}"

    def _chamar_ollama(self, provider: dict, prompt: str) -> tuple:
        try:
            req = urllib.request.Request(
                provider["url"],
                data=json.dumps({"model": provider["model"], "prompt": prompt, "stream": False}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode("utf-8"))
                ans = json.loads(res.get("response", "{}"))
                return ans.get("veredito") == "aprovado", ans.get("motivo", "Sem motivo")
        except Exception:
            return None, "Ollama nao esta a correr"

    def consultar_rede(self, patch_data: str) -> tuple:
        print("  [FEDERACAO] A convocar IAs externas para segunda opiniao...")
        prompt = self._prompt_auditoria(patch_data)

        # Ordem de preferencia: Local primeiro, depois cloud
        ordem = ["ollama", "groq", "openai", "anthropic", "deepseek"]

        for nome in ordem:
            provider = self.providers[nome]
            print(f"  [FEDERACAO] A tentar {nome.upper()}...")
            
            if nome == "ollama":
                aprovado, motivo = self._chamar_ollama(provider, prompt)
            elif nome == "anthropic":
                aprovado, motivo = self._chamar_anthropic(provider, prompt)
            else:
                aprovado, motivo = self._chamar_openai_compat(provider, prompt)

            if aprovado is not None:
                print(f"  [FEDERACAO] {nome.upper()} respondeu: {'APROVADO' if aprovado else 'REJEITADO'} ({motivo})")
                return aprovado, motivo
            else:
                print(f"  [FEDERACAO] {nome.upper()} indisponivel: {motivo}")

        print("  [FEDERACAO] Nenhuma IA externa disponivel. A confiar no Kernel Local.")
        return True, "Aprovado pelo Kernel Local (Fallback)"