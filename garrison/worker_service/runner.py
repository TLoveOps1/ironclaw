import os
import json
import subprocess
import requests
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import model_io

class WorkerRunner:
    def __init__(self, ledger_url: str, api_key: str, api_base: str):
        self.ledger_url = ledger_url
        self.api_key = api_key
        self.api_base = api_base

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
        mission_type = req_data.get("mission_type", "default")
        
        print(f"Worker starting mission_type={mission_type} run_id={run_id} order_id={order_id}")
        
        if mission_type == "filesystem_agent.call_summary":
            return self.run_filesystem_call_summary(req_data)
        else:
            return self.run_generic(req_data)

    def run_generic(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        wt_path = Path(req_data["worktree_path"])
        order_id = req_data["order_id"]
        run_id = req_data["run_id"]
        attempt = req_data["attempt"]
        mission_type = req_data.get("mission_type", "default")
        stage = "starting"
        started_at = self.utc_iso()
        
        try:
            # 0. Idempotency Check (Existing v1 logic)
            existing_head = self.check_already_completed(wt_path, order_id, attempt)
            if existing_head:
                print(f"Order {order_id} attempt {attempt} already completed. Short-circuiting.")
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
            
            # 2. Prompt Management (Repo-backed)
            prompt_template_path = req_data.get("prompt_template")
            prompt_template_commit_sha = None
            prompt_content = req_data["prompt"] # Default to message if no template
            
            if prompt_template_path:
                template_file = wt_path / "prompts" / prompt_template_path
                if template_file.exists():
                    prompt_content = template_file.read_text(encoding="utf-8")
                    # Get commit SHA of the template
                    try:
                        prompt_template_commit_sha = subprocess.check_output(
                            ["git", "rev-parse", "HEAD"], cwd=str(wt_path), text=True
                        ).strip()
                    except:
                        pass
                else:
                    print(f"Warning: Prompt template {prompt_template_path} not found in repo. Using raw prompt.")

            # Write inputs/prompt.txt (Requirement 4)
            inputs_dir = wt_path / "inputs"
            inputs_dir.mkdir(parents=True, exist_ok=True)
            (inputs_dir / "prompt.txt").write_text(prompt_content, encoding="utf-8")

            # 3. Deterministic Fingerprinting (Requirement 5)
            resolved_model_config = req_data["resolved_model_config"]
            model_id = resolved_model_config["model"]
            profile_name = resolved_model_config.get("profile_name", "unknown") # Safe get
            
            # Normalize prompt for hashing
            normalized_prompt = prompt_content.strip()
            
            fingerprint_input = {
                "model_id": model_id,
                "profile_name": profile_name,
                "prompt": normalized_prompt,
                "template_commit": prompt_template_commit_sha,
                "overrides": {k: v for k, v in resolved_model_config.items() if k not in ["model", "profile_name"]}
            }
            fingerprint = hashlib.sha256(json.dumps(fingerprint_input, sort_keys=True).encode()).hexdigest()
            
            # 4. Check Cache (Requirement 5)
            # Use theater-global cache for cross-order idempotency.
            # This lives under the theater root as Vault-owned/theater-owned state.
            theater_root = wt_path.parent.parent # theaters/{theater}
            global_cache_dir = theater_root / "vault_cache" / "intelligence"
            global_cache_dir.mkdir(parents=True, exist_ok=True)
            global_cache_file = global_cache_dir / f"output.{fingerprint}.json"
            
            # Local copy in worktree for artifact persistence
            outputs_dir = wt_path / "outputs"
            outputs_dir.mkdir(parents=True, exist_ok=True)
            local_cache_file = outputs_dir / f"model_output.{fingerprint}.json"
            
            prompt_hash = hashlib.sha256(normalized_prompt.encode()).hexdigest()
            
            if global_cache_file.exists():
                print(f"Fingerprint match: {fingerprint}. Skipping model call (Global Hit).")
                cached_data = json.loads(global_cache_file.read_text(encoding="utf-8"))
                text = cached_data["text"]
                usage = cached_data.get("usage", {})
                latency = cached_data.get("latency_ms", 0)
                cache_hit = True
                
                # Copy to local worktree for artifacts
                if not local_cache_file.exists():
                    local_cache_file.write_text(json.dumps(cached_data, indent=2), encoding="utf-8")
            else:
                # 5. Call Model
                stage = "calling_model"
                self.write_heartbeat(wt_path, stage)
                
                # Ledger: worker.model_call.started (Requirement 6)
                model_event_payload = {
                    "profile_name": profile_name,
                    "model_id": model_id,
                    "prompt_hash": prompt_hash,
                    "attempt": attempt,
                    "artifact_paths": [f"outputs/model_output.{fingerprint}.json"]
                }
                self.emit_ledger_event(req_data, "started", "worker.model_call.started", model_event_payload)
                
                try:
                    text, usage, latency = model_io.call_model(resolved_model_config, prompt_content)
                    cache_hit = False
                    
                    # Write output to both global cache and local worktree
                    output_data = {
                        "text": text,
                        "usage": usage,
                        "latency_ms": latency,
                        "fingerprint": fingerprint,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    global_cache_file.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
                    local_cache_file.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
                    
                except Exception as e:
                    # Ledger: worker.model_call.failed
                    failed_payload = {
                        **model_event_payload,
                        "error": str(e)
                    }
                    self.emit_ledger_event(req_data, "failed", "worker.model_call.failed", failed_payload)
                    raise e

            # Ledger: worker.model_call.completed (Requirement 6)
            response_hash = hashlib.sha256(text.encode()).hexdigest()
            completed_payload = {
                "profile_name": profile_name,
                "model_id": model_id,
                "prompt_hash": prompt_hash,
                "response_hash": response_hash,
                "latency_ms": latency,
                "attempt": attempt,
                "artifact_paths": [f"outputs/model_output.{fingerprint}.json"],
                "cache_hit": cache_hit
            }
            self.emit_ledger_event(req_data, "completed", "worker.model_call.completed", completed_payload)
            
            # 6. Write final AAR (Requirement 7)
            stage = "writing_artifacts"
            self.write_heartbeat(wt_path, stage)
            
            # Copy active output to default location for v1 compatibility
            (outputs_dir / "model_output.txt").write_text(text, encoding="utf-8")
            
            aar = {
                "order_id": order_id,
                "run_id": run_id,
                "mission_type": mission_type,
                "attempt": attempt,
                "status": "completed",
                "stage": "done",
                "started_at": started_at,
                "ended_at": self.utc_iso(),
                "model_profile": profile_name,
                "model_id": model_id,
                "prompt_template_path": prompt_template_path,
                "prompt_template_commit_sha": prompt_template_commit_sha,
                "prompt_hash": prompt_hash,
                "response_hash": response_hash,
                "cache_hit": cache_hit,
                "latency_ms": latency,
                "usage": usage,
                "artifacts": [
                    {"path": "inputs/prompt.txt", "type": "text/plain"},
                    {"path": f"outputs/model_output.{fingerprint}.json", "type": "application/json"},
                    {"path": "outputs/model_output.txt", "type": "text/plain"}
                ],
                "error": None
            }
            (wt_path / "aar.json").write_text(json.dumps(aar, indent=2), encoding="utf-8")
            
            # 7. Git Commit
            stage = "committing"
            self.write_heartbeat(wt_path, stage)
            subprocess.run(["git", "add", "."], cwd=str(wt_path), check=True, capture_output=True)
            subprocess.run([
                "git", "commit", "-m", f"worker: {order_id} attempt {attempt}"
            ], cwd=str(wt_path), check=True, capture_output=True)
            
            order_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(wt_path), text=True
            ).strip()
            
            # 8. Done
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
            
            try:
                failed_aar = {
                    "order_id": order_id,
                    "run_id": run_id,
                    "attempt": attempt,
                    "status": "failed",
                    "stage": stage,
                    "started_at": started_at,
                    "ended_at": self.utc_iso(),
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

    def run_filesystem_call_summary(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        wt_path = Path(req_data["worktree_path"])
        order_id = req_data["order_id"]
        run_id = req_data["run_id"]
        attempt = req_data["attempt"]
        mission_type = req_data.get("mission_type")
        resolved_model_config = req_data["resolved_model_config"]
        profile_name = resolved_model_config.get("profile_name", "unknown")
        model_id = resolved_model_config["model"]
        
        stage = "starting"
        started_at = self.utc_iso()
        
        try:
            # 0. Check completion (reuse existing)
            existing_head = self.check_already_completed(wt_path, order_id, attempt)
            if existing_head:
                print(f"Order {order_id} attempt {attempt} already completed. Short-circuiting.")
                self.emit_ledger_event(req_data, "completed", "ORDER_COMPLETED", {
                    "order_head": existing_head,
                    "stage": "done",
                    "note": "short-circuit"
                })
                return {"status": "completed", "order_head": existing_head, "stage": "done"}

            # 1. Start logic
            stage = "initializing"
            self.write_heartbeat(wt_path, stage)
            self.emit_ledger_event(req_data, "running", "ORDER_RUNNING", {"stage": stage})

            # 2. Read context
            inputs_dir = wt_path / "inputs"
            context_dir = wt_path / "context"
            
            call_content = ""
            if (inputs_dir / "call.md").exists():
                 call_content = (inputs_dir / "call.md").read_text(encoding="utf-8")
            
            account_info = "{}"
            if (context_dir / "account.json").exists():
                account_info = (context_dir / "account.json").read_text(encoding="utf-8")
                
            playbook_content = ""
            if (context_dir / "playbook.md").exists():
                playbook_content = (context_dir / "playbook.md").read_text(encoding="utf-8")

            # 3. Build Prompt
            system_prompt = (
                "You are an AI assistant processing a customer call transcript.\n"
                "Your goal is to produce a concise summary and extract actionable items.\n"
                "The user will provide the transcript and account details.\n"
                "You must respond in the following format:\n\n"
                "# Summary\n"
                "[Your summary here]\n\n"
                "---\n\n"
                "# Action Items\n"
                "- [Owner] Description\n\n"
                "Follow any specific guidance provided in the Playbook section."
            )
            
            user_prompt = (
                f"# Account Info\n{account_info}\n\n"
                f"# Playbook Guidance\n{playbook_content}\n\n"
                f"# Call Transcript\n{call_content}"
            )
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # 4. Call Model
            stage = "calling_model"
            self.write_heartbeat(wt_path, stage)
            
            prompt_hash = hashlib.sha256(full_prompt.encode()).hexdigest()
            model_event_payload = {
                "profile_name": profile_name,
                "model_id": model_id,
                "prompt_hash": prompt_hash,
                "attempt": attempt,
                "note": "filesystem_agent"
            }
            self.emit_ledger_event(req_data, "started", "worker.model_call.started", model_event_payload)
            
            text, usage, latency = model_io.call_model(resolved_model_config, full_prompt)
            
            response_hash = hashlib.sha256(text.encode()).hexdigest()
            completed_payload = {
                **model_event_payload,
                "response_hash": response_hash,
                "latency_ms": latency
            }
            self.emit_ledger_event(req_data, "completed", "worker.model_call.completed", completed_payload)

            # 5. Parse and Write Outputs
            stage = "writing_artifacts"
            self.write_heartbeat(wt_path, stage)
            
            outputs_dir = wt_path / "outputs"
            outputs_dir.mkdir(parents=True, exist_ok=True)
            
            (outputs_dir / "model_output.txt").write_text(text, encoding="utf-8")
            
            # Parsing logic
            summary = text
            action_items = "No action items parsed."
            
            parts = text.split("# Action Items")
            if len(parts) > 1:
                summary_part = parts[0]
                action_items_part = parts[1]
                
                summary_part = summary_part.replace("# Summary", "").strip()
                if summary_part.endswith("---"):
                    summary_part = summary_part[:-3].strip()
                    
                summary = summary_part
                action_items = action_items_part.strip()
            else:
                 parts = text.split("---")
                 if len(parts) > 1:
                      summary = parts[0].replace("# Summary", "").strip()
                      action_items = parts[1].replace("# Action Items", "").strip()

            (outputs_dir / "summary.md").write_text(summary, encoding="utf-8")
            (outputs_dir / "action_items.md").write_text(action_items, encoding="utf-8")
            
            # 6. AAR
            aar = {
                "order_id": order_id,
                "run_id": run_id,
                "mission_type": mission_type,
                "attempt": attempt,
                "status": "completed",
                "stage": "done",
                "started_at": started_at,
                "ended_at": self.utc_iso(),
                "model_profile": profile_name,
                "model_id": model_id,
                "prompt_hash": prompt_hash,
                "response_hash": response_hash,
                "latency_ms": latency,
                "usage": usage,
                "artifacts": [
                     {"path": "inputs/call.md", "type": "text/markdown"},
                     {"path": "outputs/summary.md", "type": "text/markdown"},
                     {"path": "outputs/action_items.md", "type": "text/markdown"},
                     {"path": "outputs/model_output.txt", "type": "text/plain"}
                ],
                "error": None
            }
            
            (wt_path / "aar.json").write_text(json.dumps(aar, indent=2), encoding="utf-8")

            # 7. Commit
            stage = "committing"
            self.write_heartbeat(wt_path, stage)
            subprocess.run(["git", "add", "."], cwd=str(wt_path), check=True, capture_output=True)
            subprocess.run([
                "git", "commit", "-m", f"worker: {order_id} attempt {attempt} (filesystem)"
            ], cwd=str(wt_path), check=True, capture_output=True)
            
            order_head = subprocess.check_output(
                 ["git", "rev-parse", "HEAD"], cwd=str(wt_path), text=True
            ).strip()

            # 8. Done
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
            
            try:
                failed_aar = {
                    "order_id": order_id,
                    "run_id": run_id,
                    "attempt": attempt,
                    "status": "failed",
                    "stage": stage,
                    "started_at": started_at,
                    "ended_at": self.utc_iso(),
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
