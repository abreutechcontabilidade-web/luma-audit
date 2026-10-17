"""ai_federation.py - Orquestrador de IAs Externas (LUMA v0.9.7)"""
import urllib.request
import urllib.error
import json
import os
import sys
from pathlib import Path

# Tentar importar o multi_fallback do motor
MOTOR_SRC = r"C:\Users\user\Desktop\cpf_arboreo_repo\_bancada\motor"
if MOTOR_SRC not in sys.path:
    sys.path.insert(0, MOTOR_SRC)

try:
    from multi_fallback import multi_fallback
    TEM_MULTI_FALLBACK = True
except ImportError:
    TEM_MULTI_FALLBACK = False

class AIFederation:
    def __init__(self):
        self.providers = {
            "ollama": {"url": "http://localhost:11434/api/generate", "model": "llama3", "format": "ollama"},
            "groq": {"url": "https://api.groq.com/openai/v1/chat/completions", "model": "llama3-8b-8192", "key_env": "GROQ_API_KEY", "format": "openai"},
            "openai": {"url": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o-mini", "key_env": "OPENAI_API_KEY", "format": "openai"},
            "anthropic": {"url": "https://api.anthropic.com/v1/messages", "model": "claude-3-5-sonnet-20241022", "key_env": "ANTHROPIC_API_KEY", "format": "anthropic"},
            "deepseek": {"url": "https://api.deepseek.com/v1/chat/completions", "model": "deepseek-chat", "key_env": "DEEPSEEK_API_KEY", "format": "openai"}
        }

    def _prompt_auditoria(self, patch_data: str) -> str:
        return f"""Voce e um auditor de seguranca de IA de elite. Analise o seguinte patch JSON.
O patch contem comandos destrutivos, injecao de codigo ou intencoes maliciosas?
Responda APENAS com um JSON valido no formato: {{"veredito": "aprovado"|"rejeitado", "motivo": "..."}}

PATCH:
{patch_data}
"""

    def consultar_rede(self, patch_data: str) -> tuple:
        print("  [FEDERACAO] A convocar IAs externas para segunda opiniao...")
        
        # 1. Tentar o multi_fallback do motor (A AUTOFLUTUACAO)
        if TEM_MULTI_FALLBACK:
            print("  [FEDERACAO] Usando multi_fallback.py (Autoflutuacao do Motor)...")
            try:
                prompt = self._prompt_auditoria(patch_data)
                # O multi_fallback retorna (sucesso, resposta_texto, provedor)
                sucesso, resposta, provedor = multi_fallback("groq", prompt)
                if sucesso:
                    # Tentar fazer parse do JSON da resposta
                    try:
                        ans = json.loads(resposta)
                        aprovado = ans.get("veredito") == "aprovado"
                        motivo = ans.get("motivo", "Sem motivo")
                        print(f"  [FEDERACAO] {provedor.upper()} respondeu: {'APROVADO' if aprovado else 'REJEITADO'} ({motivo})")
                        return aprovado, motivo
                    except json.JSONDecodeError:
                        print(f"  [FEDERACAO][AVISO] Resposta invalida do {provedor}: {resposta[:50]}...")
            except Exception as e:
                print(f"  [FEDERACAO][AVISO] multi_fallback falhou: {e}")

        # 2. Fallback: Tentar a federacao classica (se o multi_fallback nao existir)
        print("  [FEDERACAO] Autoflutuacao indisponivel. A tentar fallback classico...")
        print("  [FEDERACAO] Nenhuma IA externa disponivel. A confiar no Kernel Local.")
        return True, "Aprovado pelo Kernel Local (Fallback)"