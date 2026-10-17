# ================================================================
# luma_prompt_audit.py — v0.3 · BILÍNGUE + PONDERADO + ANTI-EVASÃO
#
# Correções vs v0.2 (lane: CTO sandbox · patch aceito pelo CTO principal
# · critérios: precision ≥ 0.80 · recall ≥ 0.70 · FPR ≤ 0.15):
#   1. ANTI-EVASÃO antes do match — só roda se o arsenal v0.2 passou
#      limpo; o caminho original fica byte-idêntico (zero regressão no
#      que já funcionava). Decodifica:
#        · NFKC + homóglifos (cirílico/grego → latino) + zero-width
#        · leetspeak contextual (1gn0r3 → ignore; só tokens mistos —
#          versões, datas e números puros intocados, FPR protegido)
#        · rot13 (involução: FPR teoricamente impossível fora de ataque)
#        · base64 inline (≥20 chars, validado, ≥90% imprimível, máx 2)
#   2. RASTREABILIDADE — motivo carrega a etiqueta da evasão:
#      "padrao hostil [norma:leetspeak]" (D74: número sem proveniência
#      não é prova).
#   3. CONTRATO INTACTO — 15 padrões, pesos, LIMIAR=1.0, vereditos
#      aprovada/rejeitada, tag "vazio", hash_de: nada de quebra.
# ================================================================
import re, base64, codecs, hashlib, unicodedata

def _sem_acentos(t: str) -> str:
    """NFD: ç → c + ¸, ã → a + ~ — o texto fica 'chato' mas comparável."""
    return ''.join(c for c in unicodedata.normalize('NFD', t)
                   if unicodedata.category(c) != 'Mn')

# ── v0.3 · arsenal anti-evasão (stdlib puro, determinístico, offline) ──

# Mapa leet conservador. Sem 9→g e sem !→i: a forense não mostrou tráfego,
# e agressividade grátis é o erro do 0.6.1a (FPR 3×) — nunca mais.
_MAPA_LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "8": "b", "@": "a", "$": "s",
})
_SIMBOLOS_LEET = "@$"

# Zero-width: o espaço que não se vê (injeção por copy-paste hostil).
_ZWSP = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)

# Homóglifos de alto tráfego (cirílico + grego) — o resto o NFKC resolve.
_HOMOGLIFOS = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
    "у": "y", "к": "k", "м": "m", "т": "t", "в": "b", "н": "h",
    "і": "i", "ѕ": "s", "ј": "j", "ԁ": "d", "ɡ": "g", "ո": "n",
    "α": "a", "ο": "o", "ε": "e", "ι": "i", "κ": "k", "ρ": "p",
    "τ": "t", "υ": "u", "ν": "v", "χ": "x", "β": "b",
    "σ": "s", "μ": "m", "п": "n",
}

# Token = runa alfanumérica (com @ $ porque leet usa símbolo por letra).
_TOKEN_LEET = re.compile(r"[A-Za-z0-9@#$]+")
_DIGITOS_LEET = set("0134578")

def _deleet(t: str) -> str:
    """Desofusca leet. Dois casos:
    · token misto (letras + dígito/@/$): '1gn0r3'→'ignore' — números,
      versões e datas intocados ('0.8.2', '10/10/2024', 'R$ 199');
    · token PURO de dígitos-leet com EXATAMENTE 2 chars: leet integral
      de conector curto — '45'→'as'. '404', '500', '1337', '199' e
      datas ficam intocados; o produto decodificado é lixo inofensivo
      que nunca vira palavra de ataque (padrões têm ≥3 letras)."""
    def _decodifica(m):
        w = m.group(0)
        if len(w) < 2:
            return w
        if any(c.isalpha() for c in w):
            if any(c.isdigit() for c in w) or any(c in _SIMBOLOS_LEET for c in w):
                return w.translate(_MAPA_LEET)
            return w
        if len(w) == 2 and all(c in _DIGITOS_LEET for c in w):
            return w.translate(_MAPA_LEET)
        return w
    return _TOKEN_LEET.sub(_decodifica, t)

def _dobra_profunda(t: str) -> str:
    """NFKC (fullwidth) + homóglifos + zero-width — o 'quase-invisível'."""
    t = unicodedata.normalize("NFKC", t)
    t = "".join(_HOMOGLIFOS.get(c, c) for c in t)
    return t.translate(_ZWSP)

# Marcadores: o atacante que ANUNCIA o codificador assina a própria pena.
_MARCADOR_CODIGO = re.compile(
    r"\b(rot ?-?13|base ?64|b64|codificad[oa]s?|decodific\w*|decript\w*|"
    r"descriptograf\w+|decifra\w*)\b", re.IGNORECASE)

# Candidato base64: ≥20 chars do alfabeto (std ou url-safe). Curto demais
# é slug de URL; o filtro imprimível no decode faz a segunda porteira.
_B64_CANDIDATO = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}|[A-Za-z0-9_-]{20,}={0,2}")

def _b64_variantes(texto: str, maximo: int = 2):
    """Decodifica blocos base64 inline. Só sobrevive o bloco que decodifica
    para UTF-8 ≥90% imprimível — hash hex, slug e ruído morrem aqui.
    Máximo 2 blocos por texto: decodificação não vira DoS (lição 0.8.0)."""
    saida = []
    for m in _B64_CANDIDATO.finditer(texto):
        if len(saida) >= maximo:
            break
        corpo = m.group(0).rstrip("=")
        if len(corpo) % 4 == 1:               # comprimento impossível em b64
            continue
        for cand in (corpo, corpo.replace("-", "+").replace("_", "/")):
            try:
                dados = base64.b64decode(cand + "=" * (-len(cand) % 4), validate=True)
                decod = dados.decode("utf-8")
            except Exception:
                continue
            if decod and sum(c.isprintable() or c in "\r\n\t"
                             for c in decod) / len(decod) >= 0.9:
                saida.append(decod)
                break
    return saida

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

    # ── v0.3 · núcleo de varredura (extraído do v0.2, semântica intacta) ──
    def _varrer(self, texto: str):
        """Um passo do arsenal. Rejeição (early-return com a tag do padrão
        que cruzou o LIMIAR) ou None. Idêntico ao loop v0.2."""
        score = 0.0
        for rx, tag, peso in self._compilados:
            if rx.search(texto):
                score += peso
                if score >= self.LIMIAR:
                    return ("rejeitada", "padrao hostil", tag)
        return None

    # ── v0.3 · geração de variantes (determinística, sem rede, sem ML) ──
    def _variantes(self, prompt: str, texto_base: str):
        """Cada variante = (texto_normalizado, etiqueta_forense).
        Ordem fixa: dobra profunda → leetspeak → rot13 → base64."""
        # 1) dobra profunda: NFKC + homóglifos + zero-width + re-normalização
        dobrado = _sem_acentos(_dobra_profunda(texto_base))
        if dobrado != texto_base:
            yield dobrado, "norma:homoglifo/zwsp"
        # 2) leetspeak contextual sobre o texto dobrado
        deleetado = _deleet(dobrado)
        if deleetado != dobrado:
            yield deleetado, "norma:leetspeak"
        # 3) rot13 — involution: um legítimo só bate aqui se CONTÉM o rot13
        #    de frase de ataque, o que é intenção, não acidente.
        #    COMPÓSITO com deleet: leet DENTRO do rot13 é o dobro de camada
        #    ("g0qnf" → rot13 → "t0das" → deleet → "todas").
        if any("a" <= c <= "z" for c in dobrado):
            yield _deleet(codecs.encode(dobrado, "rot13")), "norma:rot13"
        # 4) base64 inline — decodifica do ORIGINAL (b64 é sensível à caixa;
        #    lower() do v0.2 destruiria o alfabeto e viraria lixo indecifrável)
        if _B64_CANDIDATO.search(prompt) or _MARCADOR_CODIGO.search(prompt):
            for i, decod in enumerate(_b64_variantes(prompt), 1):
                yield _sem_acentos(decod.lower()), f"norma:base64#{i}"

    def auditar(self, prompt: str) -> tuple:
        if not isinstance(prompt, str) or len(prompt.strip()) < 5:
            return "rejeitada", "contexto vazio ou trivial", "vazio"
        # v0.2: normaliza acentos ANTES do match — encoding deixa de ser furo
        texto = _sem_acentos(prompt.lower())
        # v0.2: caminho original INTACTO — primeiro julgamento é o de sempre
        veredito = self._varrer(texto)
        if veredito is not None:
            return veredito
        # v0.3: o arsenal original passou limpo — só agora testamos evasões.
        # Um texto que bate numa variante não era legítimo por acidente:
        # estava codificado PARA ENGANAR o match.
        for texto_n, etiqueta in self._variantes(prompt, texto):
            veredito_n = self._varrer(texto_n)
            if veredito_n is not None:
                v, m, t = veredito_n
                return v, f"{m} [{etiqueta}]", t
        return "aprovada", "nenhum padrao hostil", "limpo"

    def hash_de(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
