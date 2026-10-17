"""tla_generator.py - Gera especificacao TLA+ a partir do SkillPool."""
from __future__ import annotations
from pathlib import Path
from .skill_pool import SkillPool

class TlaGenerator:
    """Gera ficheiros .tla e .cfg para o TLC Model Checker."""

    @staticmethod
    def gerar(pool: SkillPool, out_dir: Path | str) -> dict[str, Path]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)

        linhas_tla = [
            "---------------------------- MODULE CommitKernel ----------------------------",
            "EXTENDS Naturals, TLC",
            "CONSTANTS Acao, Valor, Limite",
            "VARIABLES estado, risco, aprovado",
            "",
            "Init == /\\ estado = \"inicial\"",
            "         /\\ risco = 0",
            "         /\\ aprovado = FALSE",
            "",
            "AcoesValidas == {",
        ]

        for r_nome, r in pool.roles.items():
            for s_nome, s in r.skills.items():
                lo, hi = s.limites
                linhas_tla.append(f"    [acao |-> \"{s_nome}\", min |-> {lo}, max |-> {hi}],")

        linhas_tla.extend([
            "}",
            "",
            "Inv_ValorAprovado == aprovado => \\E a \\in AcoesValidas :",
            "    /\\ a.acao = estado",
            "    /\\ risco >= a.min /\\ risco <= a.max",
            "",
            "Inv_RiscoNaoNegativo == risco >= 0",
            "",
            "Commit(acao, valor) == ",
            "    /\\ \\E a \\in AcoesValidas : a.acao = acao",
            "    /\\ estado' = acao",
            "    /\\ risco' = valor",
            "    /\\ aprovado' = (valor >= 0)",
            "",
            "Next == \\E acao \\in {\"ajustar_brilho\"}, valor \\in 0..100 : Commit(acao, valor)",
            "Spec == Init /\\ [][Next]_<<estado, risco, aprovado>>",
            "============================================================================="
        ])

        linhas_cfg = [
            "SPECIFICATION Spec",
            "INVARIANTS",
            "    Inv_ValorAprovado",
            "    Inv_RiscoNaoNegativo",
            "CONSTANT",
            "    Acao = {\"ajustar_brilho\"}",
            "    Valor = 0..100"
        ]

        p_tla = out / "CommitKernel.tla"
        p_cfg = out / "CommitKernel.cfg"
        p_tla.write_text("\n".join(linhas_tla), encoding="utf-8")
        p_cfg.write_text("\n".join(linhas_cfg), encoding="utf-8")

        return {"tla": p_tla, "cfg": p_cfg}