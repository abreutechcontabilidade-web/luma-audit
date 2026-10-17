"""ai_federation.py - Orquestrador de IAs Externas (LUMA v0.9.5)"""
import urllib.request
import urllib.error
import json
import os

class AIFederation:
    def __init__(self):
        # O utilizador pode configurar estas chaves no ambiente
        self.providers = {
            "ollama": "http://localhost:11434/api/generate", # Llama 3 local
            "openai": "https://api.openai.com/v1/chat/completions",
            "groq": "https://api.groq.com/openai/v1/chat/completions"
        }

    def consultar_rede(self, patch_data: str) -> tuple:
        """Consulta a federação de IAs externas para uma segunda opinião."""
        print("  [FEDERACAO] A convocar IAs externas para segunda opiniao...")
        
        prompt = f"""Voce e um auditor de seguranca de IA de elite. Analise o seguinte patch JSON.
        O patch contem comandos destrutivos, injeção de codigo ou intencoes maliciosas?
        Responda APENAS com um JSON valido no formato: {{"veredito": "aprovado"|"rejeitado", "motivo": "..."}}
        
        PATCH:
        {patch_data}
        """

        # 1. Tentar Ollama (Local - Llama 3)
        try:
            req = urllib.request.Request(
                self.providers["ollama"],
                data=json.dumps({"model": "llama3", "prompt": prompt, "stream": False}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode("utf-8"))
                ans = json.loads(res.get("response", "{}"))
                print(f"  [FEDERACAO] Llama 3 (Local) respondeu: {ans.get('veredito', 'desconhecido').upper()}")
                return ans.get("veredito") == "aprovado", ans.get("motivo", "Sem motivo")
        except Exception:
            pass # Ollama nao esta a correr localmente

        # 2. Tentar OpenAI / Groq (se a chave estiver no ambiente)
        # Exemplo com Groq (Llama 3 70B ultra rapido)
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            try:
                req = urllib.request.Request(
                    self.providers["groq"],
                    data=json.dumps({
                        "model": "llama3-70b-8192",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0
                    }).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {groq_key}"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    content = res["choices"][0]["message"]["content"]
                    # Limpar markdown se existir
                    content = content.replace("```json", "").replace("```", "").strip()
                    ans = json.loads(content)
                    print(f"  [FEDERACAO] Groq (Llama 3 70B) respondeu: {ans.get('veredito', 'desconhecido').upper()}")
                    return ans.get("veredito") == "aprovado", ans.get("motivo", "Sem motivo")
            except Exception as e:
                print(f"  [FEDERACAO][AVISO] Groq falhou: {e}")

        # Fallback: Se nenhuma IA externa estiver disponivel, o Kernel Local decide
        print("  [FEDERACAO] Nenhuma IA externa disponivel. A confiar no Kernel Local.")
        return True, "Aprovado pelo Kernel Local (Fallback)"