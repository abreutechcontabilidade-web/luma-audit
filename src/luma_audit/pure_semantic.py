"""pure_semantic.py - A Essência Pura do LumaProGateway (Standalone LUMA v1.0.3)
Extraído do ia_dog.py do CPF Arbóreo, mas sem dependências de SQLAlchemy ou base de dados.
Contém: Leet Decode, Trigramas, Cosseno, e a lógica de decisão baseada em LIMIAR_CONTENCAO.
"""
import math
import re
import unicodedata
from collections import Counter
from typing import Tuple

LIMIAR_CONTENCAO = 0.35

def _leet_decode(texto: str) -> str:
    # Lógica simplificada de leet (pode ser expandida com o mapa completo do original)
    leet_map = str.maketrans('431057@$', 'aeiostas')
    return texto.translate(leet_map)

def detectar_injecao_regex(prompt: str) -> bool:
    padroes = [
        r"ignore\s+(previous|all)\s+instructions",
        r"system\s*\(|exec\s*\(|eval\s*\(",
        r"fetch\s*\(|document\.cookie|XMLHttpRequest",
        r"rm\s+-rf|del\s+/q|format\s+c:",
        r"import\s+os|subprocess|sys\.exit"
    ]
    for p in padroes:
        if re.search(p, prompt, re.IGNORECASE):
            return True
    return False

class PureSemantic:
    def __init__(self):
        # Trigramas de referência (vazios por omissão, podem ser carregados de um JSON)
        self.ref_trigramas = {}

    def _normalizar(self, texto: str) -> str:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()
        texto = re.sub(r'[^a-z0-9\s]', '', texto)
        return texto

    def _trigramas(self, texto: str) -> Counter:
        texto = f" {texto} "
        return Counter(texto[i:i+3] for i in range(len(texto)-2))

    def _cosseno(self, a: Counter, b: Counter) -> float:
        intersecao = set(a) & set(b)
        numerador = sum(a[x] * b[x] for x in intersecao)
        soma_a = math.sqrt(sum(v**2 for v in a.values()))
        soma_b = math.sqrt(sum(v**2 for v in b.values()))
        if soma_a == 0 or soma_b == 0:
            return 0.0
        return numerador / (soma_a * soma_b)

    def avaliar_max_proximidade(self, prompt: str) -> Tuple[float, str]:
        # Se houver trigramas de referência, calcula o cosseno
        if self.ref_trigramas:
            prompt_norm = self._normalizar(prompt)
            prompt_tri = self._trigramas(prompt_norm)
            melhor_score = 0.0
            melhor_ref = ""
            for nome, ref in self.ref_trigramas.items():
                score = self._cosseno(prompt_tri, ref)
                if score > melhor_score:
                    melhor_score = score
                    melhor_ref = nome
            return melhor_score, melhor_ref
        return 0.0, ""

    def auditar_texto(self, payload) -> str:
        texto = str(payload)
        
        # 1. Regex de Injeção Direta
        if detectar_injecao_regex(texto):
            return "rejeitado"
            
        # 2. Leet Decode e re-verificação
        texto_leet = _leet_decode(texto)
        if detectar_injecao_regex(texto_leet):
            return "rejeitado"
            
        # 3. Cosseno com trigramas (se houver referência)
        score, _ = self.avaliar_max_proximidade(texto)
        if score > LIMIAR_CONTENCAO:
            return "rejeitado"
            
        return "aprovado"