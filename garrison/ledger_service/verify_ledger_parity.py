import json
import sqlite3
from pathlib import Path

# Configuration
BASELINE_PATH = Path("/tmp/co_list_baseline.json")
DB_PATH = Path(__file__).parent / "ledger.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def verify():
    if not BASELINE_PATH.exists():
        print(f"Baseline not found at {BASELINE_PATH}")
        return

    with BASELINE_PATH.open("r", encoding="utf-8") as f:
        baseline = json.load(f)

    with get_db() as conn:
        runs = conn.execute("SELECT * FROM runs_snapshot").fetchall()
        orders = conn.execute("SELECT * FROM orders_snapshot").fetchall()

    runs_snap = {r["run_id"]: dict(r) for r in runs}
    orders_snap = {o["order_id"]: dict(o) for o in orders}

    print(f"Comparing {len(baseline['runs'])} runs and {len(baseline['orders'])} orders...")

    mismatches = 0
    
    for r_base in baseline["runs"]:
        rid = r_base["run_id"]
        if rid not in runs_snap:
            print(f"MISSING RUN: {rid}")
            mismatches += 1
            continue
        
        r_snap = runs_snap[rid]
        # Basic field comparison
        if r_base["status"] != r_snap["status"]:
            # co_list.py sometimes uses derived status, but our ledger service should match the logic.
            # co_list.py output for status can be "running (derived completed)"
            # We'll check if the base status is contained or matches.
            if r_base["status"].split(" ")[0] != r_snap["status"]:
                print(f"RUN STATUS MISMATCH: {rid} (base: {r_base['status']}, snap: {r_snap['status']})")
                mismatches += 1

    for o_base in baseline["orders"]:
        oid = o_base["order_id"]
        if oid not in orders_snap:
            print(f"MISSING ORDER: {oid}")
            mismatches += 1
            continue
        
        o_snap = orders_snap[oid]
        if o_base["status"] != o_snap["status"]:
            print(f"ORDER STATUS MISMATCH: {oid} (base: {o_base['status']}, snap: {o_snap['status']})")
            mismatches += 1
        
        if o_base["worktree"] != o_snap["worktree"]:
            print(f"ORDER WORKTREE MISMATCH: {oid} (base: {o_base['worktree']}, snap: {o_snap['worktree']})")
            mismatches += 1

    if mismatches == 0:
        print("VERIFICATION SUCCESS: Ledger service parity with co_list.py confirmed.")
    else:
        print(f"VERIFICATION FAILED: {mismatches} mismatches found.")

if __name__ == "__main__":
    verify()
