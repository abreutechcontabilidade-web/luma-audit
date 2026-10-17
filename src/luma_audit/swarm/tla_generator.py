"""tla_generator.py - Gera especificacao TLA+ a partir do SkillPool (Fase 5)."""
from __future__ import annotations

from pathlib import Path

from .skill_pool import SkillPool


def _pool_padrao():
    """Devolve um SkillPool por omissao, tolerante a variacoes de API."""
    if hasattr(SkillPool, "default"):
        try:
            return SkillPool.default()
        except Exception:
            pass
    try:
        return SkillPool()
    except Exception:
        return None


class TlaGenerator:
    """Gera ficheiros .tla e .cfg para o TLC Model Checker."""

    @staticmethod
    def gerar(pool=None, out_dir="tla_out"):
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        if pool is None:
            pool = _pool_padrao()

        items = []  # lista de (nome, min, max)
        roles = getattr(pool, "roles", None) or {}
        for _r, role in roles.items():
            skills = getattr(role, "skills", None) or {}
            for s_nome, s in skills.items():
                try:
                    lo, hi = s.limites
                except Exception:
                    lo, hi = 0, 100
                if isinstance(s_nome, str):
                    nome = s_nome
                else:
                    nome = str(getattr(s, "nome", "acao"))
                items.append((nome, lo, hi))

        if not items:
            items.append(("ajustar_brilho", 0, 100))

        L = []
        A = L.append
        A("---------------------------- MODULE CommitKernel ----------------------------")
        A("EXTENDS Naturals, TLC")
        A("")
        A("\\* Gerado por luma-audit TlaGenerator (Fase 5).")
        A("\\* Tese: nenhuma acao fora dos limites e aprovada.")
        A("")
        A("VARIABLES estado, risco, aprovado")
        A("vars == <<estado, risco, aprovado>>")
        A("")
        A("Init ==")
        A('    /\\ estado = "inicial"')
        A("    /\\ risco = 0")
        A("    /\\ aprovado = FALSE")
        A("")
        A("\\* Acoes validas extraidas do SkillPool")
        A("AcoesValidas ==")
        A("    {")
        A(",\n".join(
            ('        [acao |-> "' + n + '", min |-> ' + str(lo) + ", max |-> " + str(hi) + "]")
            for (n, lo, hi) in items
        ))
        A("    }")
        A("")
        A("\\* Invariante 1: se aprovado, o valor esta dentro dos limites")
        A("Inv_ValorAprovado ==")
        A("    aprovado =>")
        A("    \\E a \\in AcoesValidas :")
        A("        /\\ a.acao = estado")
        A("        /\\ risco >= a.min /\\ risco <= a.max")
        A("")
        A("\\* Invariante 2: o risco nunca e negativo")
        A("Inv_RiscoNaoNegativo == risco >= 0")
        A("")
        A("Commit(acao, valor) ==")
        A("    /\\ \\E a \\in AcoesValidas : a.acao = acao")
        A("    /\\ estado' = acao")
        A("    /\\ risco' = valor")
        A("    /\\ aprovado' =")
        A("        \\E a \\in AcoesValidas :")
        A("            /\\ a.acao = acao")
        A("            /\\ valor >= a.min /\\ valor <= a.max")
        A("")
        A("Next ==")
        A('    \\E acao \\in {' + ", ".join(('"' + n + '"') for (n, _lo, _hi) in items) + "} :")
        A("        \\E valor \\in 0..100 : Commit(acao, valor)")
        A("")
        A("Spec ==")
        A("    Init /\\ [][Next]_vars")
        A("")
        A("=============================================================================")

        p_tla = out / "CommitKernel.tla"
        p_cfg = out / "CommitKernel.cfg"
        p_tla.write_text("\n".join(L) + "\n", encoding="utf-8")

        cfg = [
            "SPECIFICATION Spec",
            "INVARIANTS",
            "    Inv_ValorAprovado",
            "    Inv_RiscoNaoNegativo",
        ]
        p_cfg.write_text("\n".join(cfg) + "\n", encoding="utf-8")

        return {"tla": p_tla, "cfg": p_cfg}