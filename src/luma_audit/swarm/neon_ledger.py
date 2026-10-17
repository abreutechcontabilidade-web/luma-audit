"""neon_ledger.py - Ledger persistente na nuvem (Neon Postgres)."""
import os
import json
import psycopg2
from psycopg2.extras import Json
from .ledger import Ledger, Evento, _hash

class NeonLedger(Ledger):
    def __init__(self, db_url: str = None, head_assinada: str = None):
        # Puxa a URL do ambiente ou da instancia
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL nao definida para o NeonLedger")
        
        # Inicializa a classe base sem ficheiro (guardamos na nuvem)
        super().__init__(caminho=None, head_assinada=head_assinada)
        self._init_db()

    def _init_db(self):
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS luma_events (
                        seq INTEGER PRIMARY KEY,
                        tipo TEXT,
                        payload JSONB,
                        hash_anterior TEXT,
                        hash TEXT,
                        ts DOUBLE PRECISION
                    );
                """)
            conn.commit()
        # Carrega o estado da nuvem para a RAM
        self._carregar_neon()

    def _carregar_neon(self):
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT seq, tipo, payload, hash_anterior, hash, ts FROM luma_events ORDER BY seq ASC")
                rows = cur.fetchall()
                self.eventos = [Evento(seq=r[0], tipo=r[1], payload=r[2], hash_anterior=r[3], hash=r[4], ts=r[5]) for r in rows]
                if self.eventos:
                    self.head = self.eventos[-1].hash

    def append(self, tipo: str, payload: dict) -> Evento:
        seq = len(self.eventos) + 1
        h = _hash(seq, tipo, payload, self.head)
        ev = Evento(seq=seq, tipo=tipo, payload=payload, hash_anterior=self.head, hash=h)
        
        # Grava no Neon
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO luma_events (seq, tipo, payload, hash_anterior, hash, ts) VALUES (%s, %s, %s, %s, %s, %s)",
                    (ev.seq, ev.tipo, Json(ev.payload), ev.hash_anterior, ev.hash, ev.ts)
                )
            conn.commit()

        self.eventos.append(ev)
        self.head = h
        return ev
