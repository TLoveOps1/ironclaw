import hashlib
import json
import requests
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException

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

    def resolve_model_config(self, theater: str, model_profile: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        policy_path = Path(f"/home/tlove96/ironclaw/theaters/{theater}/repo/policy/model_policy.json")
        if not policy_path.exists():
            # Fallback to default theater if specific theater policy doesn't exist
            policy_path = Path("/home/tlove96/ironclaw/theaters/default/repo/policy/model_policy.json")
        
        if not policy_path.exists():
            raise HTTPException(status_code=500, detail=f"Model policy not found for theater {theater}")

        with policy_path.open("r", encoding="utf-8") as f:
            policy = json.load(f)

        profiles = policy.get("profiles", {})
        if model_profile not in profiles:
            raise HTTPException(status_code=400, detail=f"Unknown model profile: {model_profile}")

        config = profiles[model_profile].copy()
        
        # Apply overrides (only if in allowlist or if it's a known param)
        allowlist = policy.get("allowlist_models", [])
        if "model" in overrides:
            if overrides["model"] not in allowlist:
                raise HTTPException(status_code=400, detail=f"Model {overrides['model']} not in allowlist")
            config["model"] = overrides["model"]
        
        if "temperature" in overrides:
            config["temperature"] = overrides["temperature"]

        if "max_tokens" in overrides:
            config["max_tokens"] = overrides["max_tokens"]

        config["profile_name"] = model_profile
        
        return config

    def write_filesystem_call_summary_inputs(
        self,
        worktree_path: str,
        *,
        mission_type: str,
        run_id: str,
        order_id: str,
        request_id: str,
        theater: str,
        objective: str,
        message: str,
        overrides: dict,
    ) -> None:
        """
        Prepare the inputs/ and context/ files for the filesystem_agent.call_summary mission.

        This is a thin helper that writes files inside the Vault-provisioned worktree.
        It does not talk to external services.
        """
        root = Path(worktree_path)
        inputs_dir = root / "inputs"
        context_dir = root / "context"

        inputs_dir.mkdir(parents=True, exist_ok=True)
        context_dir.mkdir(parents=True, exist_ok=True)

        # 1) Call transcript as markdown
        call_md = (
            f"# Call Summary Mission\n\n"
            f"Mission type: {mission_type}\n"
            f"Run: {run_id}  Order: {order_id}  Request: {request_id}\n"
            f"Theater: {theater}\n"
            f"Objective: {objective}\n\n"
            f"---\n\n"
            f"{message}\n"
        )
        (inputs_dir / "call.md").write_text(call_md, encoding="utf-8")

        # 2) Mission payload as JSON
        mission_payload = {
            "mission_type": mission_type,
            "run_id": run_id,
            "order_id": order_id,
            "request_id": request_id,
            "theater": theater,
            "objective": objective,
            "overrides": overrides or {},
            "source": "co_service.chat",
        }
        (inputs_dir / "mission.json").write_text(
            json.dumps(mission_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        # 3) Fake account context (lightweight CRM-style info)
        account_name = (overrides or {}).get("account_name") or "Unknown Account"
        contact_name = (overrides or {}).get("contact_name") or "Unknown Contact"

        account_context = {
            "account_name": account_name,
            "contact_name": contact_name,
            "industry": "Unknown",
            "current_plan": "Unknown",
            "renewal_date": None,
            "account_health": "Unknown",
        }
        (context_dir / "account.json").write_text(
            json.dumps(account_context, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        # 4) Summary playbook guidance as markdown
        playbook_md = """# Summary Playbook

When summarizing a call:

1. Start with a 2–3 sentence high-level summary.
2. Explicitly list:
   - risks
   - blockers
   - commitments
3. Extract action items with:
   - owner
   - due date (if mentioned)
   - short description
"""
        (context_dir / "playbook.md").write_text(playbook_md, encoding="utf-8")
