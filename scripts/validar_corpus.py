"""validar_corpus.py - benchmark publico do luma-audit prompt_audit."""
import argparse
import csv
import sys
from pathlib import Path

from luma_audit import PromptAudit


def ler_csv(caminho, coluna="prompt"):
    out = []
    with open(caminho, "r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            v = None
            if coluna in row and row[coluna]:
                v = row[coluna]
            elif row:
                for x in row.values():
                    if x and str(x).strip():
                        v = x
                        break
            if v:
                out.append(str(v).strip())
    return out


def avaliar(textos, esperado, auditor):
    tp = fn = tn = fp = 0
    for t in textos:
        try:
            v, _, _ = auditor.auditar(t)
            rejeitada = (v == "rejeitada")
        except Exception:
            rejeitada = True
        if esperado == "ataque":
            if rejeitada: tp += 1
            else: fn += 1
        else:
            if rejeitada: fp += 1
            else: tn += 1
    return tp, fn, tn, fp


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default="corpus/raw")
    p.add_argument("--n", type=int, default=500)
    p.add_argument("--saida", default="corpus/RELATORIO.md")
    args = p.parse_args()

    base = Path(args.corpus)
    if not base.exists():
        print(f"[ERRO] pasta nao existe: {base}"); sys.exit(1)

    ataq = []
    for f in ["jailbreak_2023_12_25.csv", "jailbreak_2023_05_07.csv"]:
        fp = base / f
        if fp.exists(): ataq.extend(ler_csv(fp))
    legit = []
    for f in ["regular_2023_12_25.csv", "regular_2023_05_07.csv"]:
        fp = base / f
        if fp.exists(): legit.extend(ler_csv(fp))

    if not ataq or not legit:
        print(f"[ERRO] corpus vazio. ataq={len(ataq)} legit={len(legit)}"); sys.exit(2)

    ataq = ataq[:args.n]
    legit = legit[:args.n]
    print(f"[INFO] amostras: {len(ataq)} ataques + {len(legit)} legitimos")

    a = PromptAudit()
    tp, fn, _, _ = avaliar(ataq, "ataque", a)
    _, _, tn, fp = avaliar(legit, "legitimo", a)

    prec = tp/(tp+fp) if (tp+fp) else 0.0
    rec  = tp/(tp+fn) if (tp+fn) else 0.0
    fpr  = fp/(fp+tn) if (fp+tn) else 0.0
    acc  = (tp+tn)/(tp+fn+tn+fp) if (tp+fn+tn+fp) else 0.0

    md = [
        "# RELATORIO - validacao publica luma-audit prompt_audit",
        "",
        f"Amostras: **{len(ataq)} ataques** + **{len(legit)} legitimos**",
        "",
        "## Matriz de confusao",
        "",
        "|  | Rejeitado | Aprovado |",
        "|---|---|---|",
        f"| Ataque (esperado rejeitar) | TP={tp} | FN={fn} |",
        f"| Legitimo (esperado aprovar) | FP={fp} | TN={tn} |",
        "",
        "## Metricas",
        "",
        f"- **Precision**: {prec:.4f}",
        f"- **Recall**   : {rec:.4f}",
        f"- **FPR**      : {fpr:.4f}",
        f"- **Accuracy** : {acc:.4f}",
        "",
        "Corpus: TrustAIRLab/in-the-wild-jailbreak-prompts (publico, HF).",
    ]
    Path(args.saida).write_text(chr(10).join(md), encoding="utf-8")
    print(f"[OK] {args.saida}")
    print(f"     precision={prec:.4f} recall={rec:.4f} FPR={fpr:.4f} acc={acc:.4f}")


if __name__ == "__main__":
    main()
