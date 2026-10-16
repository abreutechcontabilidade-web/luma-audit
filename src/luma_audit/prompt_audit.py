# ================================================================
# luma_prompt_audit.py — v0.2 · BILÍNGUE + PONDERADO
#
# Correções vs v0.1:
#   1. NORMALIZAÇÃO de acentos (NFD strip) — o mojibake mata regex
#      com ç/ã/õ; normalizando ANTES do match, o encoding deixa de
#      ser vulnerabilidade.
#   2. PT-BR completo — o produto é brasileiro; o atacante local
#      passava limpo (prova: "esqueça suas instruções" = aprovada).
#   3. PONDERAÇÃO pela lei de potência real (forense 28/09):
#      "ignore previous instructions" = 45,5% dos bloqueios; top-3 = 79%.
# ================================================================
import re, hashlib, unicodedata

def _sem_acentos(t: str) -> str:
    """NFD: ç → c + ¸, ã → a + ~ — o texto fica 'chato' mas comparável."""
    return ''.join(c for c in unicodedata.normalize('NFD', t)
                   if unicodedata.category(c) != 'Mn')

class PromptAudit:
    """Recebe TEXTO, devolve veredito. Determinístico, offline, bilingue."""

    # ── TOP-3 ponderados (79% dos bloqueios reais) · EN + PT-BR ──
    PADROES = [
        # [1] 45,5% — injeção de instruções (o rei dos jailbreaks)
        (r"\b(ignore|forget|disregard|desconsidere|esqueca|esqueca-se|"
         r"apague|ignore)\s+(todas?\s+|all\s+|any\s+|as\s+)?"
         r"(as\s+)?(suas\s+)?(previous|anteriores|previas|instrucoes|"
         r"instructions|regras|rules)\b",
         "injecao_instrucoes", 3.0),
        # [2] 20,2% — personas sem filtro (amoral/uncensored/DAN...)
        (r"\b(amoral|uncensored|unfiltered|sem\s+filtro|sem\s+limites|"
         r"sem\s+etica|sem\s+regras)\b|\bDAN\b|Do\s+Anything\s+Now|"
         r"LeakGPT|\bAIM\b",
         "persona_jailbreak", 2.0),
        # [3] 12,9% — anything-now / anything-else
        (r"\bdo\s+anything\s+(now|else)\b|qualquer\s+coisa\s+agora\b",
         "anything_now", 2.0),
        # ── resto do arsenal (famílias 4-15) ──
        (r"\bwithout.{0,30}\b(restrictions?|rules?|limits?|limites)\b|"
         r"\bsem\s+(restricoes|regras|limites)\b",
         "remocao_limites", 1.0),
        (r"\bjailbreak\b", "jailbreak", 1.0),
        (r"\bdeveloper\s+mode\b|\bmodo\s+(desenvolvedor|admin)\b",
         "modo_privilegiado", 1.0),
        (r"\bforget\s+(all\s+|the\s+|any\s+)?(pre|previous)\b|"
         r"\besqueca\s+(tudo\s+)?(o\s+)?que\s+(foi\s+)?(dito|falado)\b",
         "injecao_variante", 1.0),
        (r"\bbroken\s+(the\s+)?(free\s+)?chains?\b|quebre\s+as\s+correntes\b",
         "broken_chains", 1.0),
        (r"\bdisregard\s+(all\s+|the\s+|any\s+)?(laws?|morals?|regras?|leis)\b|"
         r"\bignora\s+as?\s+(leis|regras)\b",
         "desrespeito_leis", 1.0),
        (r"\bdoes\s*n(o'|o)?t\s+(care|follow|respe\w+)\b|nao\s+(segue|respeita)\b",
         "nao_respeita", 1.0),
        (r"\bno\s+(ethical|moral|legal)\s+(guidelines?|principles?|limites)\b|"
         r"\bsem\s+(principios|etica|limites\s+eticos)\b",
         "sem_etica", 1.0),
        (r"\brules\s*=\s*\{", "config_injecao", 1.0),
        # ── famílias de conteúdo hostil (mantidas da v0.1, bilingues) ──
        (r"\bhackear|hack\s+into|invadir|roubar\s+(dados|senha|credenciais)\b",
         "cibercrime", 1.5),
        (r"\b(corromper|destruir|apagar\s+tudo|wipe)\s+(o\s+)?(sistema|dados|banco)\b",
         "destruicao", 1.5),
        (r"\bexplosiv|bomba|arma\s+de\s+fogo|receita\s+de\s+droga|sintetizar\s+droga\b",
         "ilegal_fisico", 1.5),
    ]

    LIMIAR = 1.0     # soma de pesos para rejeitar

    def __init__(self):
        self._compilados = [(re.compile(p, re.IGNORECASE), tag, w)
                            for p, tag, w in self.PADROES]

    def auditar(self, prompt: str) -> tuple:
        if not isinstance(prompt, str) or len(prompt.strip()) < 5:
            return "rejeitada", "contexto vazio ou trivial", "vazio"
        # v0.2: normaliza acentos ANTES do match — encoding deixa de ser furo
        texto = _sem_acentos(prompt.lower())
        score = 0.0
        tag_top = "limpo"
        for rx, tag, peso in self._compilados:
            if rx.search(texto):
                score += peso
                tag_top = tag if peso >= 1.0 and score == peso else tag_top
                if score >= self.LIMIAR:
                    return "rejeitada", "padrao hostil", tag
        return "aprovada", "nenhum padrao hostil", "limpo"

    def hash_de(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]