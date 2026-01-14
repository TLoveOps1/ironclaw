import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Configuration
THEATER_ROOT = Path("/home/tlove96/ironclaw/theaters/demo")
RUNS_JSONL = THEATER_ROOT / "runs.jsonl"
ORDERS_JSONL = THEATER_ROOT / "orders.jsonl"
DB_PATH = Path(__file__).parent / "ledger.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ingest():
    with get_db() as conn:
        # Ingest runs.jsonl
        if RUNS_JSONL.exists():
            print(f"Ingesting {RUNS_JSONL}...")
            with RUNS_JSONL.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    data = json.loads(line)
                    
                    run_id = data.get("run_id")
                    ts = data.get("started_at") or data.get("ended_at") or data.get("ts") or datetime.now(timezone.utc).isoformat()
                    event_id = str(uuid.uuid4()) # We don't have event IDs in JSONL, so we generate them.
                    
                    conn.execute("""
                    INSERT OR IGNORE INTO events (event_id, ts, run_id, event_type, payload)
                    VALUES (?, ?, ?, ?, ?)
                    """, (event_id, ts, run_id, "RUN_EVENT", json.dumps(data)))
        
        # Ingest orders.jsonl
        if ORDERS_JSONL.exists():
            print(f"Ingesting {ORDERS_JSONL}...")
            with ORDERS_JSONL.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    data = json.loads(line)
                    
                    run_id = data.get("run_id")
                    order_id = data.get("order_id")
                    ts = data.get("ts") or datetime.now(timezone.utc).isoformat()
                    event_id = str(uuid.uuid4())
                    
                    conn.execute("""
                    INSERT OR IGNORE INTO events (event_id, ts, run_id, order_id, event_type, payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (event_id, ts, run_id, order_id, "ORDER_EVENT", json.dumps(data)))
        
        conn.commit()
    print("Ingestion complete.")

if __name__ == "__main__":
    from database import rebuild_snapshots
    ingest()
    rebuild_snapshots()
    print("Snapshots rebuilt.")
