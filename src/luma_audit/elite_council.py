"""elite_council.py - O Conselho de Elite da Bancada do Mal (LUMA v0.9.4)"""
import re
import hashlib

class EliteCouncil:
    def __init__(self):
        self.vetos = []

    def _analisar_bits(self, patch_str: str) -> bool:
        # O Analista de Bits: Procura caracteres invisiveis ou ofuscacao binaria
        invisiveis = re.findall(r"[\u200b-\u200d\ufeff]", patch_str)
        if invisiveis:
            self.vetos.append("Bit-Analyzer: Caracteres invisiveis detetados (Zero-Width).")
            return False
        if "01010101" in patch_str or "\\x" in patch_str:
            self.vetos.append("Bit-Analyzer: Assinatura binaria/hex suspeita detetada.")
            return False
        return True

    def _analisar_pessimista(self, patch_str: str) -> bool:
        # O Pessimista: Assume que qualquer injeção de sistema é um ataque
        proibidos = ["rm -rf", "del /q", "format c:", "eval(", "exec(", "os.system", "subprocess."]
        for p in proibidos:
            if p in patch_str.lower():
                self.vetos.append(f"Pessimista: Comando destrutivo ou de execucao detetado ({p}).")
                return False
        return True

    def _analisar_cientista(self, patch_str: str) -> bool:
        # O Cientista: Exige estrutura (sem lixo ou caracteres corrompidos)
        if len(patch_str) > 500000: # 500KB
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
        # O Competidor: Tenta encontrar falhas no fluxo do motor
        if "import" in patch_str and "subprocess" in patch_str:
            self.vetos.append("Competidor: Tentativa de contornar o Kernel com importacoes maliciosas.")
            return False
        return True

    def avaliar(self, patch_str: str) -> bool:
        self.vetos = []
        
        # Assinatura do patch (O Bit/Byte)
        sha = hashlib.sha256(patch_str.encode()).hexdigest()[:16]
        print(f"  [CONSELHO] A analisar patch com SHA: {sha}")

        # Convocar o conselho
        self._analisar_bits(patch_str)
        self._analisar_pessimista(patch_str)
        self._analisar_cientista(patch_str)
        self._analisar_competidor(patch_str)

        if self.vetos:
            print("  [CONSELHO] VETO APLICADO:")
            for v in self.vetos:
                print(f"    - {v}")
            return False
            
        print("  [CONSELHO] Todos os 4 Auditores aprovaram o patch.")
        return True