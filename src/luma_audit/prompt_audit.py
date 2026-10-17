"""luma_prompt_audit.py - v0.3 (Normalizacao Anti-Evasao + Padroes)"""
import re
import hashlib
import unicodedata
import base64
import codecs

def _limpar_texto(t: str) -> str:
    # 1. Normalizacao NFKC e remocao de acentos
    t = unicodedata.normalize('NFKC', t).lower()
    # 2. Remover caracteres invisiveis (Zero-width e afins)
    t = re.sub(r"[\u200b-\u200d\ufeff]", "", t)
    # 3. ROT13 (se parecer texto normal)
    t_rot13 = codecs.decode(t, 'rot_13')
    # 4. Base64 inline (tenta decodificar blocos)
    b64_blocks = re.findall(r"([A-Za-z0-9+/]{16,}={0,2})", t)
    decoded_b64 = []
    for block in b64_blocks:
        try:
            dec = base64.b64decode(block).decode('utf-8')
            if dec.isprintable():
                decoded_b64.append(dec.lower())
        except Exception:
            pass
    # 5. Leetspeak (apenas se misturado com letras para evitar FPR em numeros)
    leet_map = str.maketrans('431057@$', 'aeiostas')
    t_leet = t.translate(leet_map)
    
    # Retorna todas as variacoes possiveis para o match
    return " ".join([t, t_rot13.lower(), t_leet] + decoded_b64)

class PromptAudit:
    PADROES = [
        # Padroes originais (mantidos)
        (r"\b(ignore|forget|disregard|desconsidere|esqueca|apague)\s+(todas?\s+|all\s+|any\s+|as\s+)?(as\s+)?(suas\s+)?(previous|anteriores|previas|instrucoes|instructions|regras|rules)\b", "injecao_instrucoes", 3.0),
        (r"\b(amoral|uncensored|unfiltered|sem\s+filtro|sem\s+limites|sem\s+etica|sem\s+regras)\b|\bDAN\b|Do\s+Anything\s+Now|LeakGPT|\bAIM\b", "persona_jailbreak", 2.0),
        (r"\bdo\s+anything\s+(now|else)\b|qualquer\s+coisa\s+agora\b", "anything_now", 2.0),
        (r"\bwithout.{0,30}\b(restrictions?|rules?|limits?|limites)\b|\bsem\s+(restricoes|regras|limites)\b", "remocao_limites", 1.0),
        (r"\bjailbreak\b", "jailbreak", 1.0),
        (r"\bdeveloper\s+mode\b|\bmodo\s+(desenvolvedor|admin)\b", "modo_privilegiado", 1.0),
        (r"\bforget\s+(all\s+|the\s+|any\s+)?(pre|previous)\b|\besqueca\s+(tudo\s+)?(o\s+)?que\s+(foi\s+)?(dito|falado)\b", "injecao_variante", 1.0),
        (r"\bbroken\s+(the\s+)?(free\s+)?chains?\b|quebre\s+as\s+correntes\b", "broken_chains", 1.0),
        (r"\bdisregard\s+(all\s+|the\s+|any\s+)?(laws?|morals?|regras?|leis)\b|\bignora\s+as?\s+(leis|regras)\b", "desrespeito_leis", 1.0),
        (r"\bdoes\s*n(o'|o)?t\s+(care|follow|respe\w+)\b|nao\s+(segue|respeita)\b", "nao_respeita", 1.0),
        (r"\bno\s+(ethical|moral|legal)\s+(guidelines?|principles?|limites)\b|\bsem\s+(principios|etica|limites\s+eticos)\b", "sem_etica", 1.0),
        (r"\brules\s*=\s*\{", "config_injecao", 1.0),
        (r"\bhackear|hack\s+into|invadir|roubar\s+(dados|senha|credenciais)\b", "cibercrime", 1.5),
        (r"\b(corromper|destruir|apagar\s+tudo|wipe)\s+(o\s+)?(sistema|dados|banco)\b", "destruicao", 1.5),
        (r"\bexplosiv|bomba|arma\s+de\s+fogo|receita\s+de\s+droga|sintetizar\s+droga\b", "ilegal_fisico", 1.5),
        # Novos padroes v0.3 (Anti-Evasao)
        (r"\byou\s+are\s+(now\s+)?(a\s+)?(based|free|unfiltered)", "roleplay_amoral", 2.5),
        (r"deveria\s+ter\s+sido\s+um\s+poema|tutorial\s+on\s+how\s+to", "framing_indireto", 1.5),
        (r"\b(no\s+filters?|no\s+boundaries|sem\s+filtros|sem\s+barreiras)\b", "sem_limites_soft", 0.8),
        (r"\b(synthesize|build|make|create|destroy|hack|matar|construir|fazer)\b.*\b(bomb|drug|weapon|arma|droga)\b", "fabricacao_ilegal", 3.0),
        (r"\b(todas\s+as\s+instrucoes|all\s+instructions)\b", "instrucoes_generico", 1.0)
    ]
    LIMIAR = 1.0

    def __init__(self):
        self._compilados = [(re.compile(p, re.IGNORECASE), tag, w) for p, tag, w in self.PADROES]

    def auditar(self, prompt: str) -> tuple:
        if not isinstance(prompt, str) or len(prompt.strip()) < 5:
            return "rejeitada", "contexto vazio ou trivial", "vazio"
        
        texto_normalizado = _limpar_texto(prompt)
        score = 0.0
        tag_top = "limpo"
        
        for rx, tag, peso in self._compilados:
            if rx.search(texto_normalizado):
                score += peso
                if score >= self.LIMIAR:
                    return "rejeitada", "padrao hostil (normalizado)", tag
        return "aprovada", "nenhum padrao hostil", "limpo"

    def hash_de(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]