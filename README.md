# luma-audit

> **Deterministic governance for AI actions. No LLM in the decision path.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](#)

---

## What it does

`luma-audit` is a deterministic execution-control layer that **approves or rejects AI actions before they happen**.

- **Deterministic** - same input, same output. Always.
- **Outside the model** - a layer the LLM cannot bypass.
- **Auditable** - every decision is hash-chained.

It does **not** filter text, detect toxicity, or replace authentication. It audits **actions**.

---

## Install

```bash
pip install luma-audit
```

---

## 30-second example

```python
from luma_audit import LUMA

auditor = LUMA()
auditor.avaliar('ler_ficheiro')      # -> aprovada
auditor.avaliar('apagar_ficheiro')   # -> rejeitada
auditor.avaliar('acao_desconhecida') # -> rejeitada (unknown = high risk)
```

---

## What it does NOT do

- Does not filter text (that is a prompt guardrail - different problem)
- Does not detect toxicity
- Does not replace authentication
- Does not use any LLM in the decision path

---

## Architecture

```
src/luma_audit/
    auditor.py       # LUMA class + Veredito enum
    trajetoria.py    # Sessao, AuditorTrajetoria, Decisao, hash chain
    canal.py         # CanalUnico, MensagemFunil
    funil.py         # FunilUnico, FILA_DIR
    cli.py           # luma CLI entrypoint
```

## Tests

22 red-team tests: hash chain integrity + tampering, quarantine escalation, flood detection, atomic writes, corrupted proposal rejection, executor revalidation.

---

## Philosophy

Guardrails based on prompts compete against the model's weights - and lose. The only layer that cannot be bypassed is the one running **outside the model**, at the point of execution.

`luma-audit` is that layer.

---

## License

MIT. Community Edition. Enterprise Edition available commercially.
