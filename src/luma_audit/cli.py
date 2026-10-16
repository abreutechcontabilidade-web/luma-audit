"""luma - CLI da luma-audit."""
import argparse
import json
import sys

from . import __version__
from .auditor import LUMA, Veredito
from .prompt_audit import PromptAudit
from .sentinela import Sentinela
from .vigia import Vigia


def cmd_audit(args):
    a = LUMA()
    proposta = {"acao": args.action, "valor": args.value}
    contexto = {"lux": args.lux, "hora": args.hora, "origem": args.origem}
    v = a.auditar(proposta, contexto)
    print(json.dumps({"proposta": proposta, "contexto": contexto,
                      "veredito": v.value}, indent=2, ensure_ascii=False))
    return 0 if v == Veredito.APROVADA else 1


def cmd_prompt(args):
    a = PromptAudit()
    veredito, motivo, tag = a.auditar(args.texto)
    resultado = {"texto": args.texto[:80], "veredito": veredito,
                 "tag": tag, "motivo": motivo,
                 "hash": a.hash_de(args.texto)}
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0 if veredito == "aprovada" else 1


def cmd_sentinela_status(args):
    s = Sentinela()
    print(json.dumps(s.status(), indent=2, ensure_ascii=False))
    print(f"cadeia integra: {s.verificar_cadeia()}")
    return 0


def cmd_sentinela_foco(args):
    s = Sentinela()
    ok = s.registrar_foco(motivo=args.motivo)
    print("[OK] foco registado" if ok else "[SKIP] ja registado hoje")
    print(json.dumps(s.status(), indent=2, ensure_ascii=False))
    return 0


def cmd_vigia_checar(args):
    r = Vigia(pasta=args.pasta).checar()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if not r["alertas"] else 1


def cmd_version(args):
    print(f"luma-audit {__version__}")
    return 0


def main():
    p = argparse.ArgumentParser(prog="luma",
        description="Auditoria deterministica de acoes de IA.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("audit")
    pa.add_argument("--action", required=True,
                    choices=["ajustar_brilho", "ajustar_gamma"])
    pa.add_argument("--value", type=float, required=True)
    pa.add_argument("--lux", type=int, required=True)
    pa.add_argument("--hora", required=True)
    pa.add_argument("--origem", default="SENSOR",
                    choices=["SENSOR", "DECLARADO"])
    pa.set_defaults(func=cmd_audit)

    pp = sub.add_parser("prompt")
    pp.add_argument("--texto", required=True)
    pp.set_defaults(func=cmd_prompt)

    ps = sub.add_parser("sentinela")
    ss = ps.add_subparsers(dest="sub", required=True)
    ss.add_parser("status").set_defaults(func=cmd_sentinela_status)
    sf = ss.add_parser("foco")
    sf.add_argument("--motivo", default="interacao")
    sf.set_defaults(func=cmd_sentinela_foco)

    pv = sub.add_parser("vigia")
    sv = pv.add_subparsers(dest="sub", required=True)
    vc = sv.add_parser("checar")
    vc.add_argument("--pasta", default=".")
    vc.set_defaults(func=cmd_vigia_checar)

    pver = sub.add_parser("version")
    pver.set_defaults(func=cmd_version)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
