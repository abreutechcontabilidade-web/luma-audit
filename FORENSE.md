# 🔴 PERÍCIA FORENSE HOSTIL — luma-audit

**Data:** 17/10/2026 · **Método:** lente de adversário · **Versão auditada:** 0.8.1

> Auditoria adversarial deliberada: encontrar tudo o que um perito hostil
> pode usar contra o projeto — técnico, reputacional, legal, supply-chain.
> Publicada de propósito. D4: o Museu registra facto com prova, não narrativa.

---

## Técnicos (exploráveis hoje)

| # | Achado | Cura | Estado |
|---|---|---|---|
| A1 | Fail-closed DoS: sensor inativo paralisa swarm | `fail-open` opcional + alerta | 📋 backlog |
| A2 | HMAC com chave literal nos testes (`b"chave"`) | `SensorBinding` recusa chaves < 32 bytes / baixa entropia | ⏳ 0.8.2 |
| A3 | `SkillPool.default()` sem tenant scope | `SkillPool.for_tenant(scope)` obrigatório | ⏳ 0.8.2 |
| A4 | `Ledger` sem head assinada — truncation attack | `Ledger(head_assinada=...)` + validação externa | ⏳ 0.8.2 |
| A5 | Replay verifica hashes, não policy | `verificar_ledger` aceita `policy@version` | 📋 0.9.0 |
| A6 | Lib sem assinatura própria | Wheel hash publicado em `RELEASES.md` | 📋 0.9.0 |
| A7 | Timing side-channel em `validar` | Uniformização de tempo (evaluate-then-return) | 📋 0.9.0 |

## Reputacionais

| # | Achado | Mitigação |
|---|---|---|
| F1 | "Determinismo é marketing" | RELATORIO público com números reproduzíveis |
| F2 | Kevros tem compliance; nós não | Mapeamento OWASP Agentic 2026 no README |
| F3 | Recall 0.56 publicamente fraco | Honestidade radical: "primeiro filtro, não gate único" |
| F4 | ESTUDO-SENIOR como auto-elogio | Reforço: citação de standards + papers externos |
| F5 | 5 releases num dia | Freeze 0.8.x → 0.9.0 com breaking change planeado |
| F6 | Incoerências de versão | `__version__` = `pyproject.toml` verificado no CI |

## Legais / Regulatórios

| # | Achado | Estado |
|---|---|---|
| L1 | Corpus redistribuído | ✅ **Nunca entrou no git history** (verificado 17/10) |
| L2 | "Governança" sem compliance | 📋 mapeamento OWASP Agentic 2026 na 0.9.0 |
| L3 | Chave literal em `tests/` | ⏳ A2 fecha na 0.8.2 |
| L4 | Claims sem disclaimer | Adicionar secção "Limitations" no README |

## Supply Chain

| # | Achado | Estado |
|---|---|---|
| S1 | Token PyPI mantido por decisão do fundador | Aceito · escopo project-specific a rotar |
| S2 | Typo-squat possível (`luma_audit`, `luma-audlt`) | 📋 reservar nomes no PyPI |
| S3 | CI sem pinning | ✅ **Pinado por SHA** (`970e3c31`) |

## O que sobrevive

- ✅ Prova empírica pública (RELATORIO.md, corpus TrustAIRLab)
- ✅ Integridade epistémica (D4, D46, D76 — canonizadas no Museu)
- ✅ `cpf_arboreo` em produção (utilizadores reais)
- ✅ Stdlib puro (sem supply-chain de deps)
- ✅ Arquitetura swarm (4 camadas académicas juntas)
- ✅ Replay verifiable (mesmo com truncation attack — a cura está identificada)

## Metodologia

Esta perícia foi executada pelo CTO-IA como exercício adversarial
explícito. Não é uma auditoria independente. É um relatório interno
publicado pelo próprio autor — o que é raro, e por isso mesmo útil.

A resposta a cada achado é verificável no código. Achados sem cura
estão no roadmap. Nada aqui é aspiracional.

---

**Metodologia canónica:** D77 (link ou lead), D76 (verificar o próprio golpe),
D4 (facto com prova), D83 (não julgar pela janela).
