import hashlib
import json
import requests
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class COLogic:
    def __init__(self, ledger_url: str, vault_url: str, worker_url: str):
        self.ledger_url = ledger_url
        self.vault_url = vault_url
        self.worker_url = worker_url

    def derive_ids(self, request_id: Optional[str]) -> Tuple[str, str, str]:
        if request_id:
            h = hashlib.sha256(request_id.encode()).hexdigest()
            run_id = f"run_{h[:16]}"
            order_id = f"order_{h[:16]}"
            internal_request_id = request_id
        else:
            internal_request_id = str(uuid.uuid4())
            ts = int(os.environ.get("CURRENT_TIME_TS", 0)) # Placeholder or use real ts
            run_id = f"run_{ts}" if ts else f"run_{internal_request_id[:8]}"
            order_id = f"order_{ts}" if ts else f"order_{internal_request_id[:8]}"
        
        return run_id, order_id, internal_request_id

    def emit_event(self, run_id: str, order_id: str, request_id: str, event_type: str, payload: Dict[str, Any], attempt: int = 1):
        # Match Worker's event_id scheme for terminal events to ensure deduplication
        if event_type == "ORDER_COMPLETED":
            event_id = f"{request_id}-completed"
        elif event_type == "ORDER_FAILED":
            event_id = f"{request_id}-failed"
        else:
            # sha256(f"{request_id}:{event_type}:{run_id}:{order_id}:{attempt}")[:32]
            seed = f"{request_id}:{event_type}:{run_id}:{order_id}:{attempt}"
            event_id = hashlib.sha256(seed.encode()).hexdigest()[:32]
        
        event = {
            "event_id": event_id,
            "run_id": run_id,
            "order_id": order_id,
            "event_type": event_type,
            "payload": payload
        }
        
        try:
            requests.post(f"{self.ledger_url}/events", json=event, timeout=5)
        except Exception as e:
            print(f"CO failed to emit ledger event: {e}")

    def provision_worktree(self, theater: str, order_id: str) -> str:
        resp = requests.post(f"{self.vault_url}/worktrees", json={
            "theater": theater,
            "order_id": order_id
        }, timeout=10)
        resp.raise_for_status()
        return resp.json()["path"]

    def execute_worker(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(f"{self.worker_url}/execute", json=req_data, timeout=900)
        resp.raise_for_status()
        return resp.json()

    def cleanup_vault(self, theater: str, order_id: str) -> Optional[str]:
        resp = requests.post(f"{self.vault_url}/worktrees/{theater}/{order_id}/remove", timeout=30)
        resp.raise_for_status()
        return resp.json().get("archive_path")

    def read_artifact(self, worktree_path: str, relative_path: str) -> str:
        full_path = Path(worktree_path) / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {relative_path}")
        return full_path.read_text(encoding="utf-8")
    
    def read_aar(self, worktree_path: str) -> Dict[str, Any]:
        aar_path = Path(worktree_path) / "aar.json"
        if not aar_path.exists():
            raise FileNotFoundError("aar.json not found in worktree")
        return json.loads(aar_path.read_text(encoding="utf-8"))

    def get_order_snapshot(self, order_id: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.ledger_url}/orders/{order_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None
