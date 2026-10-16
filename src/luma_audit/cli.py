"""
luma — CLI da luma-audit.

Uso:
    luma audit --action ajustar_brilho --value 80 --lux 5000 --hora 14h
    luma version
    luma --help
"""
import argparse
import json
import sys

from . import __version__
from .auditor import LUMA, Veredito


def cmd_audit(args):
    auditor = LUMA()
    proposta = {"acao": args.action, "valor": args.value}
    contexto = {"lux": args.lux, "hora": args.hora}
    veredito = auditor.auditar(proposta, contexto)
    resultado = {
        "proposta": proposta,
        "contexto": contexto,
        "veredito": veredito.value,
        "aprovada": veredito == Veredito.APROVADA,
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0 if veredito == Veredito.APROVADA else 1


def cmd_version(args):
    print(f"luma-audit {__version__}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="luma",
        description="Auditoria determinística de ações de IA."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_audit = sub.add_parser("audit", help="Audita uma proposta de ação.")
    p_audit.add_argument("--action", required=True,
                          choices=["ajustar_brilho", "ajustar_gamma"],
                          help="Ação proposta.")
    p_audit.add_argument("--value", type=float, required=True,
                          help="Valor numérico da ação.")
    p_audit.add_argument("--lux", type=int, required=True,
                          help="Leitura do sensor de luz (lux).")
    p_audit.add_argument("--hora", required=True,
                          help="Hora local no formato 'Xh' (ex: 14h).")
    p_audit.set_defaults(func=cmd_audit)

    p_ver = sub.add_parser("version", help="Mostra a versão.")
    p_ver.set_defaults(func=cmd_version)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()