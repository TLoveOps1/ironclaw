import os
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timezone
from openai import OpenAI
from typing import Dict, Any, List, Optional

class WorkerRunner:
    def __init__(self, ledger_url: str, api_key: str, api_base: str):
        self.ledger_url = ledger_url
        self.api_key = api_key
        self.api_base = api_base
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def utc_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def write_heartbeat(self, wt_path: Path, stage: str):
        hb_path = wt_path / "outputs" / "heartbeat.json"
        hb_path.parent.mkdir(parents=True, exist_ok=True)
        with hb_path.open("w", encoding="utf-8") as f:
            json.dump({"ts": self.utc_iso(), "stage": stage}, f)

    def emit_ledger_event(self, req_data: Dict[str, Any], status: str, event_type: str, payload_extra: Dict[str, Any] = None):
        # Idempotency: request_id maps to event_id
        event_id = f"worker-{req_data['order_id']}-{req_data['attempt']}-{status}"
        if req_data.get("request_id"):
            event_id = f"{req_data['request_id']}-{status}"
        
        payload = {
            "status": status,
            "attempt": req_data["attempt"],
            "run_id": req_data["run_id"],
            "order_id": req_data["order_id"],
            "worktree": req_data["worktree_path"],
            **(payload_extra or {})
        }
        
        event = {
            "event_id": event_id,
            "run_id": req_data["run_id"],
            "order_id": req_data["order_id"],
            "event_type": event_type,
            "payload": payload
        }
        
        try:
            requests.post(f"{self.ledger_url}/events", json=event, timeout=5)
        except Exception as e:
            print(f"Failed to emit ledger event: {e}")

    def check_already_completed(self, wt_path: Path, order_id: str, attempt: int) -> Optional[str]:
        # Short-circuit behavior: if aar.json exists + status=completed + git commit matches
        aar_path = wt_path / "aar.json"
        if aar_path.exists():
            try:
                aar = json.loads(aar_path.read_text())
                if aar.get("status") == "completed" and aar.get("attempt") == attempt:
                    # Check if commit exists
                    order_head = subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=str(wt_path), text=True
                    ).strip()
                    return order_head
            except:
                pass
        return None

    def run(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        wt_path = Path(req_data["worktree_path"])
        order_id = req_data["order_id"]
        run_id = req_data["run_id"]
        attempt = req_data["attempt"]
        stage = "starting"
        started_at = self.utc_iso()
        
        try:
            # 0. Idempotency Check
            existing_head = self.check_already_completed(wt_path, order_id, attempt)
            if existing_head:
                print(f"Order {order_id} attempt {attempt} already completed. Short-circuiting.")
                # Re-emit completion event to be sure
                self.emit_ledger_event(req_data, "completed", "ORDER_COMPLETED", {
                    "order_head": existing_head,
                    "stage": "done",
                    "note": "short-circuit"
                })
                return {"status": "completed", "order_head": existing_head, "stage": "done"}

            # 1. Start
            stage = "initializing"
            self.write_heartbeat(wt_path, stage)
            self.emit_ledger_event(req_data, "running", "ORDER_RUNNING", {"stage": stage})
            
            # 2. Write order files (deterministic overwrite)
            (wt_path / "order.json").write_text(json.dumps({
                "order_id": order_id,
                "run_id": run_id,
                "attempt": attempt,
                "objective": req_data["objective"],
                "prompt": req_data["prompt"],
                "model": req_data["model"],
                "temperature": req_data["temperature"]
            }, indent=2), encoding="utf-8")
            
            (wt_path / "task.md").write_text(f"# {order_id}\n\n{req_data['objective']}\n", encoding="utf-8")

            # 3. Call Model
            stage = "calling_model"
            self.write_heartbeat(wt_path, stage)
            
            response = self.client.chat.completions.create(
                model=req_data["model"],
                messages=[{"role": "user", "content": req_data["prompt"]}],
                temperature=req_data["temperature"],
            )
            text = response.choices[0].message.content
            
            stage = "model_returned"
            self.write_heartbeat(wt_path, stage)
            
            # 4. Write Artifacts (atomic promotion logic)
            stage = "writing_artifacts"
            self.write_heartbeat(wt_path, stage)
            
            out_dir = wt_path / "outputs"
            out_dir.mkdir(parents=True, exist_ok=True)
            tmp_out = out_dir / "_tmp_model_output.txt"
            tmp_out.write_text(text, encoding="utf-8")
            
            aar = {
                "order_id": order_id,
                "run_id": run_id,
                "attempt": attempt,
                "status": "completed",
                "stage": "done",
                "started_at": started_at,
                "ended_at": self.utc_iso(),
                "model": {"name": req_data["model"], "temperature": req_data["temperature"]},
                "artifacts": [{"path": "outputs/model_output.txt", "type": "text/plain"}],
                "error": None
            }
            tmp_aar = wt_path / "_tmp_aar.json"
            tmp_aar.write_text(json.dumps(aar, indent=2), encoding="utf-8")
            
            # Promote
            tmp_out.replace(out_dir / "model_output.txt")
            tmp_aar.replace(wt_path / "aar.json")
            
            # 5. Git Commit
            stage = "committing"
            self.write_heartbeat(wt_path, stage)
            subprocess.run(["git", "add", "."], cwd=str(wt_path), check=True, capture_output=True)
            subprocess.run([
                "git", "commit", "-m", f"worker: {order_id} attempt {attempt}"
            ], cwd=str(wt_path), check=True, capture_output=True)
            
            order_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(wt_path), text=True
            ).strip()
            
            # 6. Done
            stage = "done"
            self.write_heartbeat(wt_path, stage)
            self.emit_ledger_event(req_data, "completed", "ORDER_COMPLETED", {
                "order_head": order_head,
                "stage": stage,
                "artifacts": aar["artifacts"]
            })
            
            return {"status": "completed", "order_head": order_head, "stage": stage}

        except Exception as e:
            error_msg = str(e)
            print(f"Worker failed at stage {stage}: {error_msg}")
            
            # Write failed AAR (Locked Schema)
            try:
                failed_aar = {
                    "order_id": order_id,
                    "run_id": run_id,
                    "attempt": attempt,
                    "status": "failed",
                    "stage": stage,
                    "started_at": started_at,
                    "ended_at": self.utc_iso(),
                    "model": {"name": req_data["model"], "temperature": req_data["temperature"]},
                    "artifacts": [],
                    "error": error_msg
                }
                (wt_path / "aar.json").write_text(json.dumps(failed_aar, indent=2), encoding="utf-8")
            except:
                pass
                
            self.emit_ledger_event(req_data, "failed", "ORDER_FAILED", {
                "error": error_msg,
                "stage": stage
            })
            return {"status": "failed", "error": error_msg, "stage": stage}
