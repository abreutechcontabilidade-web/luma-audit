# Corpus de validacao

## Fonte

Os CSVs em `raw/` vem do dataset publico
**TrustAIRLab/in-the-wild-jailbreak-prompts** (HuggingFace).

- `jailbreak_2023_05_07.csv`, `jailbreak_2023_12_25.csv` -> ataques reais
- `regular_2023_05_07.csv`, `regular_2023_12_25.csv` -> prompts legitimos

## Como regenerar

```bash
pip install datasets
python -c "from datasets import load_dataset; load_dataset(\"TrustAIRLab/in-the-wild-jailbreak-prompts\", \"jailbreak_2023_12_25\", split=\"train\").to_csv(\"corpus/raw/jailbreak_2023_12_25.csv\")"
```

## Como validar

```bash
python scripts/validar_corpus.py --n 500
```

Escreve `corpus/RELATORIO.md` com precision/recall/FPR.
