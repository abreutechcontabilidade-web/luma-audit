# luma-audit

**Governança determinística no ponto de execução.**

A LUMA audita **ações** de IA — não o texto que ela produz.
A camada de decisão não usa LLM. É determinística.
O propositor (Gemini, Claude, Llama, nenhum) é substituível.

---

## O problema

Agentes de IA já estão agindo em sistemas reais: ajustando
configurações, chamando APIs, movendo dados, tomando decisões.
A vanguarda de 2026 documentou dezenas de casos de **escape
de sandbox, colusão entre agentes, e execução de ações fora do
envelope autorizado**. Guardrails baseados em texto (prompt,
Constitutional AI) competem contra os pesos do modelo — e
perdem. A única camada que não pode ser contornada é a que
roda **fora do modelo**, no ponto de execução.

## A solução

A `luma-audit` é essa camada. Uma CLI — e futuramente uma API —
que recebe uma **proposta de ação** e o **contexto do sensor**,
e retorna um veredito determinístico: `aprovada` ou `rejeitada`.

Nenhuma decisão passa pela IA. Nenhum resultado depende de
probabilidade. O auditor aplica limites físicos declarados
e é auditável por hash chain.

## Instalação

### Requisitos
- Python 3.10 ou superior
- Windows, Linux ou macOS

### Windows / Linux / macOS — instalação local (dev)

```bash
git clone https://github.com/seu-usuario/luma-audit.git
cd luma-audit
pip install -e .