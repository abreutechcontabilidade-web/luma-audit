import tempfile
from pathlib import Path
from luma_audit.swarm import SkillPool, TlaGenerator

def teste_tla_geracao():
    out = Path(tempfile.mkdtemp())
    pool = SkillPool.default()
    paths = TlaGenerator.gerar(pool, out)
    assert paths["tla"].exists()
    assert paths["cfg"].exists()
    texto = paths["tla"].read_text(encoding="utf-8")
    assert "MODULE CommitKernel" in texto
    assert "Inv_ValorAprovado" in texto
    assert "Inv_RiscoNaoNegativo" in texto
    cfg = paths["cfg"].read_text(encoding="utf-8")
    assert "INVARIANTS" in cfg
