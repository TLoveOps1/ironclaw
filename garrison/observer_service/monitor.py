import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import requests
from datetime import datetime, timezone

class IronClawMonitor:
    def __init__(self, config: Dict[str, Any], signals: Any):
        self.config = config
        self.signals = signals
        self.ledger_url = config["ledger_url"]
        self.vault_url = config["vault_url"]
        self.theater = config["theater"]
        self.theater_root = Path(os.environ.get("IRONCLAW_THEATER_ROOT", "/home/tyler/dev/ironclaw/theaters"))
        self.stats = {
            "last_poll": 0,
            "active_runs": 0,
            "stalled_detected": 0,
            "orphans_detected": 0,
            "integrity_failures": 0,
            "alerts_emitted": 0
        }

    def poll(self):
        print(f"Observer polling theater: {self.theater}")
        self.stats["last_poll"] = time.time()
        
        # 1. Fetch active snapshots from Ledger
        try:
            # We assume Ledger has /orders for a theater or we iterate
            # For MVP, we'll fetch all orders and filter by theater and status
            resp = requests.get(f"{self.ledger_url}/events", timeout=10)
            resp.raise_for_status()
            events = resp.json()
            # Derive latest snapshots (simplified internal logic or fetch from snapshots table if API exists)
            # CO uses /orders/{order_id} but doesn't have a bulk list.
            # Let's assume we fetch all events and group them to find currently 'running' orders.
            self.check_stalls_and_integrity(events)
        except Exception as e:
            print(f"Monitor failed to reach Ledger: {e}")

        # 2. Check Orphans
        self.check_orphans()

    def check_stalls_and_integrity(self, events: List[Dict[str, Any]]):
        if not isinstance(events, list):
            print(f"Monitor expected list of events, got {type(events)}")
            return

        # Group events by order_id
        orders = {}
        for ev in events:
            if not isinstance(ev, dict): continue
            oid = ev.get("order_id")
            if not oid: continue
            if oid not in orders: orders[oid] = []
            orders[oid].append(ev)

        active_count = 0
        for oid, evs in orders.items():
            # Get latest status for this order
            evs.sort(key=lambda x: x["id"]) 
            latest = evs[-1]
            # Payload is stored as a JSON string in Ledger
            payload = latest.get("payload", {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except:
                    payload = {}
            
            status = payload.get("status")
            theater = payload.get("theater") or self.theater # Fallback
            
            if theater != self.theater: continue

            if status == "running":
                active_count += 1
                self.verify_stall(oid, latest, evs, payload)
            elif status == "completed":
                self.verify_integrity(oid, latest, payload)

        self.stats["active_runs"] = active_count

    def verify_stall(self, order_id: str, latest_ev: Dict[str, Any], all_evs: List[Dict[str, Any]], payload: Dict[str, Any]):
        # 1. Stall by lack of event progress
        try:
            last_ts = datetime.fromisoformat(latest_ev["ts"].replace("Z", "+00:00"))
            now_ts = datetime.now(timezone.utc)
            delta = (now_ts - last_ts).total_seconds()
            
            if delta > self.config["stall_seconds"]:
                if self.signals.emit("stalled", f"Order {order_id} stalled for {int(delta)}s", 
                                    run_id=latest_ev.get("run_id"), order_id=order_id,
                                    payload_extra={"delta_seconds": delta, "last_status": "running"}):
                    self.stats["stalled_detected"] += 1
                    self.stats["alerts_emitted"] += 1
        except Exception as e:
            print(f"Stall check error for {order_id}: {e}")

    def verify_integrity(self, order_id: str, latest_ev: Dict[str, Any], payload: Dict[str, Any]):
        # Integrity Gate: Check worktree and artifacts
        worktree = payload.get("worktree")
        if not worktree:
            return 

        wt_path = Path(worktree)
        if not wt_path.exists():
            # If it's archived, this is expected if ENABLE_VAULT_CLEANUP was on
            # But normally completed orders still have their worktree until archived
            # We skip if it looks missing because it might have been cleaned up by CO
            return

        # Check aar.json (non-negotiable Phase C)
        aar_path = wt_path / "aar.json"
        if not aar_path.exists():
            if self.signals.emit("integrity_failed", f"Completed order {order_id} missing aar.json",
                                run_id=latest_ev.get("run_id"), order_id=order_id,
                                payload_extra={"missing": "aar.json", "worktree": str(wt_path)}):
                self.stats["integrity_failures"] += 1
                self.stats["alerts_emitted"] += 1
                return

        # Git check (read-only)
        try:
            res = subprocess.run(["git", "status", "--porcelain"], cwd=str(wt_path), capture_output=True, text=True)
            if res.stdout.strip():
                # Uncommitted changes in a 'completed' worktree is a red flag
                 if self.signals.emit("integrity_failed", f"Completed order {order_id} has uncommitted changes",
                                    run_id=latest_ev.get("run_id"), order_id=order_id,
                                    payload_extra={"git_status": res.stdout.strip()}):
                    self.stats["integrity_failures"] += 1
                    self.stats["alerts_emitted"] += 1
        except:
            pass

    def check_orphans(self):
        # Scan filesystem
        wt_root = self.theater_root / self.theater / "worktrees"
        if not wt_root.exists(): return
        
        try:
            # Get list of existing worktree dirs
            dirs = [d.name for d in wt_root.iterdir() if d.is_dir()]
            
            # For each dir, check Ledger for active status
            for order_id in dirs:
                # In MVP, we fetch single order snapshot from Ledger
                try:
                    resp = requests.get(f"{self.ledger_url}/orders/{order_id}", timeout=5)
                    if resp.status_code == 404:
                        self.emit_orphan(order_id, str(wt_root / order_id), "Order ID not found in Ledger")
                    elif resp.status_code == 200:
                        snapshot = resp.json()
                        status = snapshot.get("status")
                        if status in {"completed", "failed"}:
                            # If it's terminal and old, it's a candidate for cleanup if CO didn't do it
                            # OR if keep_worktree was true. Observer only alerts.
                            pass # Or implement ORPHAN_TTL_SECONDS
                except:
                    pass
        except Exception as e:
            print(f"Orphan scan error: {e}")

    def emit_orphan(self, order_id: str, path: str, reason: str):
        if self.signals.emit("orphan_worktree", f"Detected orphan worktree: {order_id} ({reason})",
                            order_id=order_id, payload_extra={"path": path}):
            self.stats["orphans_detected"] += 1
            self.stats["alerts_emitted"] += 1
            
            if self.config.get("enable_vault_cleanup"):
                # Call Vault’s existing endpoints
                try:
                    requests.post(f"{self.vault_url}/worktrees/{self.theater}/{order_id}/remove", timeout=10)
                except Exception as e:
                    print(f"Observer failed to trigger Vault cleanup for orphan {order_id}: {e}")
