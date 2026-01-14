from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import json
import sqlite3
from datetime import datetime, timezone
import uuid

from database import get_db, init_db, rebuild_snapshots
from models import EventCreate, RunSnapshotModel, OrderSnapshotModel

app = FastAPI(title="IronClaw Ledger Service")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/events")
async def create_event(event: EventCreate):
    event_id = event.event_id or str(uuid.uuid4())
    ts = event.ts or datetime.now(timezone.utc).isoformat()
    
    with get_db() as conn:
        try:
            conn.execute("""
            INSERT INTO events (event_id, ts, run_id, order_id, event_type, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (event_id, ts, event.run_id, event.order_id, event.event_type, json.dumps(event.payload)))
            conn.commit()
        except sqlite3.IntegrityError:
            # Idempotency: return success if event already exists
            return {"status": "exists", "event_id": event_id}
            
    # Trigger an incremental snapshot update or just wait for explicit rebuild for now
    # For MVP, we'll just allow explicit rebuild or rebuild on read if needed.
    # Actually, let's just rebuild for now to keep it simple, or provide a flag.
    rebuild_snapshots()
    
    return {"status": "created", "event_id": event_id}

@app.get("/events")
async def list_events(
    run_id: Optional[str] = None,
    order_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    query = "SELECT * FROM events WHERE 1=1"
    params = []
    if run_id:
        query += " AND run_id = ?"
        params.append(run_id)
    if order_id:
        query += " AND order_id = ?"
        params.append(order_id)
    
    query += " ORDER BY ts DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

@app.get("/runs", response_model=List[RunSnapshotModel])
async def list_runs():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM runs_snapshot ORDER BY started_at DESC").fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["order_ids"] = json.loads(d["order_ids"])
            out.append(d)
        return out

@app.get("/runs/{run_id}", response_model=RunSnapshotModel)
async def get_run(run_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM runs_snapshot WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
        d = dict(row)
        d["order_ids"] = json.loads(d["order_ids"])
        return d

@app.get("/orders/{order_id}", response_model=OrderSnapshotModel)
async def get_order(order_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM orders_snapshot WHERE order_id = ?", (order_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        d = dict(row)
        d["extra"] = json.loads(d["extra"])
        return d

@app.post("/rebuild")
async def trigger_rebuild():
    rebuild_snapshots()
    return {"status": "rebuilt"}
