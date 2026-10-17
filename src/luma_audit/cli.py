"""luma - CLI da luma-audit."""
import argparse
import json
import sys

from . import __version__
from .auditor import LUMA, Veredito
from .prompt_audit import PromptAudit
from .sentinela import Sentinela
from .vigia import Vigia
from .replay import verificar_ledger
from .swarm import (Ledger, SkillPool, SensorBinding,
                          CommitKernel)


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


def cmd_replay(args):
    info = verificar_ledger(args.ledger)
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0 if info["integro"] else 1


def cmd_swarm_demo(args):
    import tempfile
    import os
    from pathlib import Path as _P
    
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        from .swarm.neon_ledger import NeonLedger
        # Remove channel_binding se existir para evitar conflitos no Windows
        db_url = db_url.replace("&channel_binding=require", "")
        L = NeonLedger(db_url=db_url)
        print("[!] Modo Nuvem: Ligado ao Neon DB")
    else:
        L = Ledger(_P(tempfile.mkdtemp()) / "swarm.json")
        print("[!] Modo Local: Ledger temporario")
    S = SensorBinding(b"0123456789abcdef0123456789abcdef")
    K = CommitKernel(SkillPool.default(), S, L)
    r = S.ler("bh1750", 5000)
    ctx = {"sensor_nome": r.nome, "sensor_valor": r.valor,
           "sensor_ts": r.ts, "sensor_sig": r.assinatura}
    if args.quantum:
        from .swarm.qubit_adapter import QubitAdapter
        QA = QubitAdapter(K)
        res = QA.commit_qubit(args.role, {"skill": args.skill, "valor": args.valor}, ctx, peso_bias=args.bias)
    else:
        res = K.commit(args.role, {"skill": args.skill, "valor": args.valor}, ctx)
    print(json.dumps({"ok": res.ok, "motivo": res.motivo,
                      "hash": res.evento_hash}, indent=2, ensure_ascii=False))
    return 0 if res.ok else 1



def cmd_trajetoria_simular(args):
    from .trajetoria import Sessao, AuditorTrajetoria
    a = AuditorTrajetoria()
    s = Sessao("cli-sim")
    contexto = {"lux": 500, "hora": "12h", "origem": "SENSOR"}
    print(f"Simulando {args.n} acoes de '{args.acao}'...")
    for i in range(args.n):
        proposta = {"acao": args.acao, "valor": 50.0}
        v, s = a.auditar(proposta, contexto, s)
        status = "OK" if v == "aprovada" else "BLOQUEADA"
        print(f"  Acao {i+1:02d}: {status:9s} | {v}")
        if v != "aprovada":
            print(f"\n[!] Defesa ativada na acao {i+1}. Motivo: {v}")
            break
    print(f"\nCadeia integra: {s.verificar_cadeia()}")
    return 0


def cmd_evolution(args):
    import os
    from .evolution.zbit import MemoriaZ
    from .evolution.aria_skills import EquipeAria, Skill
    from .evolution.adapter import EvolutionaryAdapter
    from .swarm.skill_pool import SkillPool
    from .swarm.sensor_binding import SensorBinding
    from .swarm.commit_kernel import CommitKernel
    
    # Configuracao do Ledger
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        from .swarm.neon_ledger import NeonLedger
        db_url = db_url.replace("&channel_binding=require", "")
        L = NeonLedger(db_url=db_url)
        print("[!] Modo Nuvem: Ligado ao Neon DB")
    else:
        from .swarm.ledger import Ledger
        L = Ledger()
        print("[!] Modo Local: Ledger em memoria")

    # Dummy Skill para teste
    class AjustarBrilhoSkill(Skill):
        def propor(self, contexto):
            return {"skill": "ajustar_brilho", "valor": 85.0}

    mem = MemoriaZ()
    equipe = EquipeAria(mem)
    sk = AjustarBrilhoSkill("ajustar_brilho")
    equipe.registrar(sk, reputacao0=0.5)

    S = SensorBinding(b"0123456789abcdef0123456789abcdef")
    K = CommitKernel(SkillPool.default(), S, L)
    adapter = EvolutionaryAdapter(equipe, K, L)

    r = S.ler("bh1750", 5000)
    ctx = {"sensor_nome": r.nome, "sensor_valor": r.valor,
           "sensor_ts": r.ts, "sensor_sig": r.assinatura}
    
    print(f"Skill '{sk.nome}' vai propor...")
    res = adapter.commit_evolutivo(sk.nome, ctx, role="luz")
    
    print(f"\nResultado: {'APROVADA' if res.ok else 'REJEITADA'} ({res.motivo})")
    print(f"Reputacao da Skill (Z-bit): {equipe.reputacao(sk):.2f}")
    print(f"Hash Ledger: {res.evento_hash}")
    return 0


def cmd_sentinela_nuvem(args):
    import os
    from .swarm.neon_ledger import NeonLedger
    from .swarm.ledger import Ledger
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[!] ERRO: DATABASE_URL nao definida. Sentinela apenas funciona na nuvem.")
        return 1
        
    db_url = db_url.replace("&channel_binding=require", "")
    print("[!] Sentinela Branco: A verificar integridade da hash chain no Neon DB...")
    
    try:
        L = NeonLedger(db_url=db_url)
        integro = L.verificar()
        
        if integro:
            print(f"[OK] LEDGER SEGURO: {len(L.eventos)} eventos verificados. Head: {L.head}")
            return 0
        else:
            print("[ALERTA CRITICO] TAMPERING DETETADO! A hash chain foi corrompida.")
            return 1
    except Exception as e:
        print(f"[ERRO FATAL] Falha ao ligar ao Sentinela: {e}")
        return 1

def cmd_shadow(args):
    import os
    from .prompt_audit import PromptAudit
    from .swarm.neon_ledger import NeonLedger
    
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        db_url = db_url.replace("&channel_binding=require", "")
        L = NeonLedger(db_url=db_url)
    else:
        from .swarm.ledger import Ledger
        L = Ledger()

    a = PromptAudit()
    veredito, motivo, tag = a.auditar(args.texto)
    
    # Regista no ledger o que TERIA acontecido
    tipo_evento = "shadow_rejeicao" if veredito == "rejeitada" else "shadow_aprovacao"
    L.append(tipo_evento, {"texto": args.texto[:50], "motivo": motivo, "tag": tag})
    
    print(f"[SHADOW] Analise concluida. Auditoria real seria: {veredito.upper()}")
    if veredito == "rejeitada":
        print(f"[!] ALERTA: Jailbreak detetado no modo sombra. Motivo: {motivo}")
    else:
        print(f"[OK] Texto limpo.")
        
    print(f"[*] Evento '{tipo_evento}' gravado na nuvem com sucesso.")
    return 0


def cmd_tla_generate(args):
    from .swarm.tla_generator import TlaGenerator
    from .swarm.skill_pool import SkillPool
    pool = SkillPool.default()
    paths = TlaGenerator.gerar(pool, args.out_dir)
    print(f"Gerado: {paths['tla']}")
    print(f"Gerado: {paths['cfg']}")
    return 0

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
    sn = ss.add_parser("nuvem", help="Verifica integridade do NeonLedger")
    sn.set_defaults(func=cmd_sentinela_nuvem)

    pv = sub.add_parser("vigia")
    sv = pv.add_subparsers(dest="sub", required=True)
    vc = sv.add_parser("checar")
    vc.add_argument("--pasta", default=".")
    vc.set_defaults(func=cmd_vigia_checar)

    # replay
    p_rep = sub.add_parser("replay", help="Verifica integridade do ledger.")
    p_rep.add_argument("--ledger", required=True)
    p_rep.set_defaults(func=cmd_replay)

    # swarm (demo)
    p_sw = sub.add_parser("swarm", help="Commit kernel (demo).")
    p_sw.add_argument("--role", default="luz")
    p_sw.add_argument("--skill", default="ajustar_brilho")
    p_sw.add_argument("--valor", type=float, default=80.0)
    p_sw.add_argument("--quantum", action="store_true", help="Usa QubitAdapter (L7)")
    p_sw.add_argument("--bias", type=float, default=0.0, help="Peso de bias para o gate (-1 a 1)")
    p_sw.set_defaults(func=cmd_swarm_demo)

    # trajetoria
    p_tr = sub.add_parser("trajetoria", help="Simula risco acumulado (L2)")
    sub_tr = p_tr.add_subparsers(dest="sub", required=True)
    p_tr_sim = sub_tr.add_parser("simular")
    p_tr_sim.add_argument("--n", type=int, default=15, help="Numero de acoes")
    p_tr_sim.add_argument("--acao", default="ajustar_brilho")
    p_tr_sim.set_defaults(func=cmd_trajetoria_simular)

    # evolution
    p_evo = sub.add_parser("evolution", help="Motor evolutivo (ARIA + Zbits)")
    p_evo.set_defaults(func=cmd_evolution)
    # shadow
    p_sh = sub.add_parser("shadow", help="Modo sombra (audita mas nao bloqueia)")
    p_sh.add_argument("--texto", required=True)
    p_sh.set_defaults(func=cmd_shadow)


    # tla
    p_tla = sub.add_parser("tla", help="Verificacao formal TLA+")
    sub_tla = p_tla.add_subparsers(dest="sub", required=True)
    p_tla_gen = sub_tla.add_parser("generate")
    p_tla_gen.add_argument("--out-dir", default="tla_out")
    p_tla_gen.set_defaults(func=cmd_tla_generate)

    pver = sub.add_parser("version")
    pver.set_defaults(func=cmd_version)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
