import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "ledger.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE,
            ts TEXT NOT NULL,
            run_id TEXT,
            order_id TEXT,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS runs_snapshot (
            run_id TEXT PRIMARY KEY,
            status TEXT,
            message TEXT,
            started_at TEXT,
            ended_at TEXT,
            order_ids TEXT,
            max_orders INTEGER,
            worktree TEXT,
            order_head TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS orders_snapshot (
            order_id TEXT PRIMARY KEY,
            run_id TEXT,
            status TEXT,
            ts TEXT,
            worktree TEXT,
            unit_head TEXT,
            order_head TEXT,
            extra TEXT
        )
        """)
    print("Database initialized.")

def rebuild_snapshots():
    with get_db() as conn:
        conn.execute("DELETE FROM runs_snapshot")
        conn.execute("DELETE FROM orders_snapshot")
        
        events = conn.execute("SELECT * FROM events ORDER BY ts ASC, id ASC").fetchall()
        
        runs = {}
        orders = {}
        
        for ev in events:
            payload = json.loads(ev["payload"])
            run_id = ev["run_id"]
            order_id = ev["order_id"]
            
            if run_id:
                if run_id not in runs:
                    runs[run_id] = {
                        "run_id": run_id,
                        "status": "-",
                        "message": "-",
                        "started_at": None,
                        "ended_at": None,
                        "order_ids": [],
                        "max_orders": None,
                        "worktree": "-",
                        "order_head": "-"
                    }
                r = runs[run_id]
                
                # Merge logic similar to co_list.py
                sa = payload.get("started_at")
                if sa:
                    if not r["started_at"] or sa < r["started_at"]:
                        r["started_at"] = sa
                
                ea = payload.get("ended_at")
                if ea:
                    if not r["ended_at"] or ea > r["ended_at"]:
                        r["ended_at"] = ea
                
                msg = payload.get("message")
                if msg: r["message"] = msg
                
                oids = payload.get("order_ids")
                if isinstance(oids, list) and oids:
                    r["order_ids"] = list(set(r["order_ids"] + [str(x) for x in oids]))
                
                mo = payload.get("max_orders")
                if mo is not None: r["max_orders"] = mo
                
                wt = payload.get("worktree")
                if wt: r["worktree"] = wt
                
                oh = payload.get("order_head")
                if oh: r["order_head"] = oh
                
                st = payload.get("status")
                if st: r["status"] = st

            if order_id:
                if order_id not in orders:
                    orders[order_id] = {
                        "order_id": order_id,
                        "run_id": run_id or "-",
                        "status": "-",
                        "ts": ev["ts"],
                        "worktree": "-",
                        "unit_head": "-",
                        "order_head": "-",
                        "extra": {}
                    }
                o = orders[order_id]
                st = payload.get("status")
                if st:
                    o["status"] = st
                    o["ts"] = ev["ts"]
                
                rid = payload.get("run_id")
                if rid: o["run_id"] = rid
                
                wt = payload.get("worktree")
                if wt: o["worktree"] = wt
                
                uh = payload.get("unit_head")
                if uh: o["unit_head"] = uh
                
                oh = payload.get("order_head")
                if oh: o["order_head"] = oh
                
                # Extras
                for k, v in payload.items():
                    if k in {"ts", "run_id", "order_id", "status", "worktree", "unit_head", "order_head", "message", "started_at", "ended_at", "order_ids", "max_orders"}:
                        continue
                    o["extra"][k] = v

        # Write snapshots
        for rid, r in runs.items():
            conn.execute("""
            INSERT INTO runs_snapshot (run_id, status, message, started_at, ended_at, order_ids, max_orders, worktree, order_head)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (r["run_id"], r["status"], r["message"], r["started_at"], r["ended_at"], json.dumps(r["order_ids"]), r["max_orders"], r["worktree"], r["order_head"]))
            
        for oid, o in orders.items():
            conn.execute("""
            INSERT INTO orders_snapshot (order_id, run_id, status, ts, worktree, unit_head, order_head, extra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (o["order_id"], o["run_id"], o["status"], o["ts"], o["worktree"], o["unit_head"], o["order_head"], json.dumps(o["extra"])))

if __name__ == "__main__":
    init_db()
