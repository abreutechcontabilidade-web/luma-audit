# RELATORIO - validacao publica luma-audit prompt_audit

Amostras: **500 ataques** + **500 legitimos**

## Matriz de confusao

|  | Rejeitado | Aprovado |
|---|---|---|
| Ataque (esperado rejeitar) | TP=281 | FN=219 |
| Legitimo (esperado aprovar) | FP=74 | TN=426 |

## Metricas

- **Precision**: 0.7915
- **Recall**   : 0.5620
- **FPR**      : 0.1480
- **Accuracy** : 0.7070

Corpus: TrustAIRLab/in-the-wild-jailbreak-prompts (publico, HF).