"""
luma - CLI da luma-audit.

Uso:
    luma audit --action ajustar_brilho --value 80 --lux 5000 --hora 14h
    luma sentinela status
    luma sentinela foco --motivo "manha"
    luma vigia checar
    luma version
    luma --help
"""
import argparse
import json
import sys

from . import __version__
from .auditor import LUMA, Veredito
from .prompt_audit import PromptAudit
from .sentinela import Sentinela
from .vigia import Vigia


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


def cmd_sentinela_status(args):
    s = Sentinela()
    print(json.dumps(s.status(), indent=2, ensure_ascii=False))
    print(f"cadeia integra: {s.verificar_cadeia()}")
    print(f"hoje registado: {s.verificar_hoje()}")
    return 0


def cmd_sentinela_foco(args):
    s = Sentinela()
    registado = s.registrar_foco(motivo=args.motivo)
    if registado:
        print(f"[OK] foco registado: {args.motivo}")
    else:
        print("[SKIP] foco ja registado hoje")
    print(json.dumps(s.status(), indent=2, ensure_ascii=False))
    return 0


def cmd_vigia_checar(args):
    v = Vigia(pasta=args.pasta)
    r = v.checar()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if not r["alertas"] else 1


def cmd_prompt(args):
    a = PromptAudit()
    veredito, motivo, tag = a.auditar(args.texto)
    resultado = {
        "texto": args.texto[:80],
        "veredito": veredito,
        "tag": tag,
        "motivo": motivo,
        "hash": a.hash_de(args.texto),
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return 0 if veredito == "aprovada" else 1

def cmd_version(args):
    print(f"luma-audit {__version__}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="luma",
        description="Auditoria deterministica de acoes de IA."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # audit
    p_audit = sub.add_parser("audit", help="Audita uma proposta de acao.")
    p_audit.add_argument("--action", required=True,
                         choices=["ajustar_brilho", "ajustar_gamma"],
                         help="Acao proposta.")
    p_audit.add_argument("--value", type=float, required=True,
                         help="Valor numerico da acao.")
    p_audit.add_argument("--lux", type=int, required=True,
                         help="Leitura do sensor de luz (lux).")
    p_audit.add_argument("--hora", required=True,
                         help="Hora local no formato 'xh' (ex: 14h).")
    p_audit.set_defaults(func=cmd_audit)
    # prompt
    p_prompt = sub.add_parser("prompt", help="Audita texto/prompt.")
    p_prompt.add_argument("--texto", required=True,
                          help="Texto a auditar.")
    p_prompt.set_defaults(func=cmd_prompt)
    # sentinela
    p_sent = sub.add_parser("sentinela", help="Contador de dias com foco.")
    sub_sent = p_sent.add_subparsers(dest="sub", required=True)
    p_sent_status = sub_sent.add_parser("status", help="Estado atual.")
    p_sent_status.set_defaults(func=cmd_sentinela_status)
    p_sent_foco = sub_sent.add_parser("foco", help="Registrar foco de hoje.")
    p_sent_foco.add_argument("--motivo", default="interacao",
                             help="Motivo do foco (default: interacao).")
    p_sent_foco.set_defaults(func=cmd_sentinela_foco)

    # vigia
    p_vig = sub.add_parser("vigia", help="Monitor de sistema.")
    sub_vig = p_vig.add_subparsers(dest="sub", required=True)
    p_vig_checar = sub_vig.add_parser("checar", help="Verificar disco/mem/pasta.")
    p_vig_checar.add_argument("--pasta", default=".",
                              help="Pasta a inspecionar (default: .).")
    p_vig_checar.set_defaults(func=cmd_vigia_checar)

    # version
    p_ver = sub.add_parser("version", help="Mostra a versao.")
    p_ver.set_defaults(func=cmd_version)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
