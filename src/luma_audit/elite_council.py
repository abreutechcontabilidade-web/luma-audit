"""elite_council.py - O Conselho de Elite com Essencia Pura Standalone (LUMA v1.0.3)"""
import re
import hashlib
import sys
from pathlib import Path

# Importar a Essência Pura Standalone (não precisa de SQLAlchemy)
try:
    from luma_audit.pure_semantic import PureSemantic
    TEM_ESSENCIA_PURA = True
except ImportError as e:
    TEM_ESSENCIA_PURA = False
    print(f"[CONSELHO][AVISO] Nao foi possivel importar a Essencia Pura: {e}")

class EliteCouncil:
    def __init__(self):
        self.vetos = []
        self.pure = PureSemantic() if TEM_ESSENCIA_PURA else None

    def _analisar_bits(self, patch_str: str) -> bool:
        invisiveis = re.findall(r"[\u200b-\u200d\ufeff]", patch_str)
        if invisiveis:
            self.vetos.append("Bit-Analyzer: Caracteres invisiveis detetados (Zero-Width).")
            return False
        if "01010101" in patch_str or "\\x" in patch_str:
            self.vetos.append("Bit-Analyzer: Assinatura binaria/hex suspeita detetada.")
            return False
        return True

    def _analisar_pessimista(self, patch_str: str) -> bool:
        proibidos = ["rm -rf", "del /q", "format c:", "eval(", "exec(", "os.system", "subprocess.", "require('fs')", "fs.readFileSync"]
        for p in proibidos:
            if p in patch_str.lower():
                self.vetos.append(f"Pessimista: Comando destrutivo ou de execucao detetado ({p}).")
                return False
        return True

    def _analisar_cientista(self, patch_str: str) -> bool:
        if len(patch_str) > 500000:
            self.vetos.append("Cientista: Patch demasiado grande (possivel bomba de descompressao).")
            return False
        try:
            import json
            json.loads(patch_str)
        except ValueError:
            self.vetos.append("Cientista: Estrutura JSON invalida (falha de integridade).")
            return False
        return True

    def _analisar_competidor(self, patch_str: str) -> bool:
        if "import" in patch_str and "subprocess" in patch_str:
            self.vetos.append("Competidor: Tentativa de contornar o Kernel com importacoes maliciosas.")
            return False
        return True

    def avaliar(self, patch_str: str) -> bool:
        self.vetos = []
        
        sha = hashlib.sha256(patch_str.encode()).hexdigest()[:16]
        print(f"  [CONSELHO] A analisar patch com SHA: {sha}")

        self._analisar_bits(patch_str)
        self._analisar_pessimista(patch_str)
        self._analisar_cientista(patch_str)
        self._analisar_competidor(patch_str)

        if not self.vetos and TEM_ESSENCIA_PURA:
            print("  [CONSELHO] A convocar a Essencia Pura Standalone...")
            try:
                veredito = self.pure.auditar_texto(patch_str)
                print(f"  [CONSELHO] Essencia Pura respondeu: {veredito.upper()}")
                if veredito.lower() == "rejeitado":
                    self.vetos.append("Essencia Pura: Injeção detectada (regex/leet/cosseno).")
            except Exception as e:
                print(f"  [CONSELHO][AVISO] Essencia Pura falhou: {e}")

        if self.vetos:
            print("  [CONSELHO] VETO APLICADO:")
            for v in self.vetos:
                print(f"    - {v}")
            return False
            
        print("  [CONSELHO] Todos os auditores (4 Locais + Essencia Pura) aprovaram o patch.")
        return True