"""key_pool.py - Gestor de Pool de Chaves com Rotacao (LUMA v0.9.7)"""
import json
from pathlib import Path

class KeyPool:
    def __init__(self):
        self.keys = {"groq": [], "openai": [], "anthropic": [], "deepseek": []}
        self._carregar_chaves()

    def _carregar_chaves(self):
        # 1. Tentar ler os vaults JSON
        vault_paths = [
            Path(r"C:\Users\user\Desktop\cpf_arboreo_repo\_bancada\motor\lib\vault.json"),
            Path(r"C:\Users\user\Desktop\zbit-omega-v2\vault.json"),
            Path(r"C:\Users\user\Desktop\LUMA\vault.json")
        ]
        for vp in vault_paths:
            if vp.exists():
                try:
                    data = json.loads(vp.read_text(encoding="utf-8"))
                    for k, v in data.items():
                        if isinstance(v, str) and len(v) > 10:
                            k_lower = k.lower()
                            if "groq" in k_lower: self.keys["groq"].append(v)
                            elif "openai" in k_lower or "gpt" in k_lower: self.keys["openai"].append(v)
                            elif "anthropic" in k_lower or "claude" in k_lower: self.keys["anthropic"].append(v)
                            elif "deepseek" in k_lower: self.keys["deepseek"].append(v)
                except Exception as e:
                    print(f"  [KEYPOOL][AVISO] Erro ao ler {vp.name}: {e}")

        # 2. Tentar ler os ficheiros TXT
        txt_paths = [
            Path(r"C:\Users\user\Desktop\LUMA\chaves.txt"),
            Path(r"C:\Users\user\Desktop\zbit-omega-v2\chaves.txt"),
            Path(r"C:\Users\user\Desktop\cpf_arboreo_repo\_bancada\motor\chaves.txt")
        ]
        for tp in txt_paths:
            if tp.exists():
                try:
                    for line in tp.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Formato esperado: provider:key ou apenas a key
                            if ":" in line:
                                provider, key = line.split(":", 1)
                                provider = provider.lower().strip()
                                if provider in self.keys: self.keys[provider].append(key.strip())
                            elif line.startswith("gsk_"): self.keys["groq"].append(line)
                            elif line.startswith("sk-ant-"): self.keys["anthropic"].append(line)
                            elif line.startswith("sk-"): self.keys["openai"].append(line)
                except Exception as e:
                    print(f"  [KEYPOOL][AVISO] Erro ao ler {tp.name}: {e}")

    def obter_chave(self, provider: str):
        """Retira uma chave do pool (rotacao)."""
        if self.keys.get(provider):
            return self.keys[provider].pop(0) # Puxa do inicio da fila
        return None

    def status(self):
        return {k: len(v) for k, v in self.keys.items()}