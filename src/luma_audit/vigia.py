"""VIGIA - monitor de sistema (disco + memoria + pasta).

Portado de teste_bender_ver/vigia.py para luma-audit 0.4.0.
Stdlib puro. Fallbacks cross-platform.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def _memoria() -> dict:
    """Windows via ctypes; Linux via /proc/meminfo; fallback null."""
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        total = m.ullTotalPhys / (1024 ** 3)
        livre = m.ullAvailPhys / (1024 ** 3)
        return {"total_gb": round(total, 2), "livre_gb": round(livre, 2), "uso_pct": round(m.dwMemoryLoad, 1)}
    except Exception:
        pass

    try:
        info = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                k, v = line.split(":", 1)
                info[k.strip()] = int(v.strip().split()[0])
        total = info["MemTotal"] / (1024 ** 2)
        livre = info["MemAvailable"] / (1024 ** 2)
        uso = round((1 - livre / total) * 100, 1)
        return {"total_gb": round(total, 2), "livre_gb": round(livre, 2), "uso_pct": uso}
    except Exception:
        return {"total_gb": None, "livre_gb": None, "uso_pct": None}


def _disco(caminho: str = ".") -> dict:
    try:
        u = shutil.disk_usage(caminho)
        total = u.total / (1024 ** 3)
        livre = u.free / (1024 ** 3)
        uso = (u.used / u.total) * 100 if u.total else 0
        return {"total_gb": round(total, 2), "livre_gb": round(livre, 2), "uso_pct": round(uso, 1)}
    except Exception:
        return {"total_gb": None, "livre_gb": None, "uso_pct": None}


def _pasta(caminho: str = ".") -> dict:
    p = Path(caminho)
    if not p.exists():
        return {"n_py": 0, "tamanho_mb": 0.0}
    n_py = 0
    total = 0
    for f in p.rglob("*.py"):
        n_py += 1
        try:
            total += f.stat().st_size
        except Exception:
            pass
    return {"n_py": n_py, "tamanho_mb": round(total / (1024 ** 2), 2)}


class Vigia:
    """Monitor deterministico de recursos do sistema."""

    def __init__(self, pasta: str = ".", lim_disco: float = 90.0,
                 lim_mem: float = 85.0, lim_py_mb: float = 50.0):
        self.pasta = pasta
        self.lim_disco = lim_disco
        self.lim_mem = lim_mem
        self.lim_py_mb = lim_py_mb

    def checar(self) -> dict:
        d = _disco(self.pasta)
        m = _memoria()
        p = _pasta(self.pasta)
        alertas = []
        if d["uso_pct"] is not None and d["uso_pct"] >= self.lim_disco:
            alertas.append(f"disco:{d['uso_pct']}%>=limite({self.lim_disco}%)")
        if m["uso_pct"] is not None and m["uso_pct"] >= self.lim_mem:
            alertas.append(f"memoria:{m['uso_pct']}%>=limite({self.lim_mem}%)")
        if p["tamanho_mb"] >= self.lim_py_mb:
            alertas.append(f"pasta_py:{p['tamanho_mb']}MB>=limite({self.lim_py_mb}MB)")
        return {"disco": d, "memoria": m, "pasta": p, "alertas": alertas}
