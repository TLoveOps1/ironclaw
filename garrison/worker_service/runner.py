import os
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timezone
from openai import OpenAI
from typing import Dict, Any, List

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
        event_id = f"worker-{req_data['order_id']}-{req_data['attempt']}-{status}"
        if req_data.get("request_id"):
            event_id = f"{req_data['request_id']}-{status}"
        
        payload = {
            "status": status,
            "attempt": req_data["attempt"],
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

    def run(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        wt_path = Path(req_data["worktree_path"])
        order_id = req_data["order_id"]
        
        try:
            # 1. Start
            self.write_heartbeat(wt_path, "starting")
            self.emit_ledger_event(req_data, "running", "ORDER_RUNNING")
            
            # 2. Write order files (idempotent)
            (wt_path / "order.json").write_text(json.dumps({
                "order_id": order_id,
                "objective": req_data["objective"],
                "prompt": req_data["prompt"],
                "model": req_data["model"],
                "temperature": req_data["temperature"]
            }, indent=2), encoding="utf-8")
            
            (wt_path / "task.md").write_text(f"# {order_id}\n\n{req_data['objective']}\n", encoding="utf-8")

            # 3. Call Model
            self.write_heartbeat(wt_path, "calling_model")
            
            response = self.client.chat.completions.create(
                model=req_data["model"],
                messages=[{"role": "user", "content": req_data["prompt"]}],
                temperature=req_data["temperature"],
            )
            text = response.choices[0].message.content
            
            self.write_heartbeat(wt_path, "model_returned")
            
            # 4. Write Artifacts (atomic promotion logic)
            self.write_heartbeat(wt_path, "writing_artifacts")
            
            out_dir = wt_path / "outputs"
            out_dir.mkdir(parents=True, exist_ok=True)
            tmp_out = out_dir / "_tmp_model_output.txt"
            tmp_out.write_text(text, encoding="utf-8")
            
            aar = {
                "order_id": order_id,
                "status": "completed",
                "started_at": self.utc_iso(), # Simplified for MVP
                "ended_at": self.utc_iso(),
                "summary": req_data["objective"],
                "artifacts": [{"path": "outputs/model_output.txt", "type": "text/plain"}],
                "model": {"name": req_data["model"], "temperature": req_data["temperature"]}
            }
            tmp_aar = wt_path / "_tmp_aar.json"
            tmp_aar.write_text(json.dumps(aar, indent=2), encoding="utf-8")
            
            # Promote
            tmp_out.replace(out_dir / "model_output.txt")
            tmp_aar.replace(wt_path / "aar.json")
            
            # 5. Git Commit
            self.write_heartbeat(wt_path, "committing")
            subprocess.run(["git", "add", "."], cwd=str(wt_path), check=True)
            subprocess.run([
                "git", "commit", "-m", f"worker: {order_id} attempt {req_data['attempt']}"
            ], cwd=str(wt_path), check=True)
            
            order_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(wt_path), text=True
            ).strip()
            
            # 6. Done
            self.write_heartbeat(wt_path, "done")
            self.emit_ledger_event(req_data, "completed", "ORDER_COMPLETED", {
                "order_head": order_head,
                "artifacts": aar["artifacts"]
            })
            
            return {"status": "completed", "order_head": order_head}

        except Exception as e:
            error_msg = str(e)
            print(f"Worker failed: {error_msg}")
            
            # Write failed AAR if possible
            try:
                failed_aar = {
                    "order_id": order_id,
                    "status": "failed",
                    "error": error_msg,
                    "ended_at": self.utc_iso()
                }
                (wt_path / "aar.json").write_text(json.dumps(failed_aar, indent=2), encoding="utf-8")
            except:
                pass
                
            self.emit_ledger_event(req_data, "failed", "ORDER_FAILED", {"error": error_msg})
            return {"status": "failed", "error": error_msg}
