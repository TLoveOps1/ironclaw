from fastapi import FastAPI, HTTPException
import os
import time
from pathlib import Path
from models import ChatRequest, ChatResponse
from logic import COLogic
from playbooks import get_playbook

app = FastAPI(title="IronClaw CO Service")

# Configuration
LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8010")
VAULT_URL = os.environ.get("VAULT_URL", "http://127.0.0.1:8011")
WORKER_URL = os.environ.get("WORKER_URL", "http://127.0.0.1:8012")
THEATER = os.environ.get("THEATER", "demo")
KEEP_WORKTREE = os.environ.get("KEEP_WORKTREE", "false").lower() == "true"
STALL_SECONDS = int(os.environ.get("WORKER_DEFAULT_STALL_SECONDS", 300))
HARD_TIMEOUT = int(os.environ.get("WORKER_DEFAULT_HARD_TIMEOUT_SECONDS", 900))

logic = COLogic(ledger_url=LEDGER_URL, vault_url=VAULT_URL, worker_url=WORKER_URL)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    theater = req.theater or THEATER
    run_id, order_id, request_id = logic.derive_ids(req.request_id)
    
    # 0. Idempotency Check (Ledger-First)
    snapshot = logic.get_order_snapshot(order_id)
    if snapshot and snapshot.get("status") == "completed":
        print(f"Order {order_id} already completed according to Ledger. Short-circuiting.")
        extra = snapshot.get("extra", {})
        return ChatResponse(
            run_id=run_id,
            order_id=order_id,
            status="completed",
            answer=extra.get("answer"),
            order_head=snapshot.get("order_head"),
            archive_path=extra.get("archive_path")
        )

    objective = req.objective or f"Process chat: {req.message[:50]}..."
    keep_wt = req.keep_worktree if req.keep_worktree is not None else KEEP_WORKTREE
    
    # Playbook lookup (v0 integration)
    # We peek into model_overrides to see if a mission_type was requested,
    # since we cannot modify the ChatRequest schema yet.
    mission_type = req.model_overrides.get("mission_type", "default")
    playbook = get_playbook(mission_type)
    if playbook:
        print(f"DEBUG: Planning with playbook: {playbook.mission_type} - {playbook.description}")
    
    # 1. Emit Initial Events
    # ...
    logic.emit_event(run_id, order_id, request_id, "RUN_CREATED", {"message": req.message})
    logic.emit_event(run_id, order_id, request_id, "ORDER_CREATED", {"theater": theater, "objective": objective})
    logic.emit_event(run_id, order_id, request_id, "ORDER_QUEUED", {})
    
    worktree_path = None
    order_head = None
    archive_path = None
    
    try:
        # 2. Provision Worktree
        logic.emit_event(run_id, order_id, request_id, "ORDER_WORKTREE_REQUESTED", {})
        worktree_path = logic.provision_worktree(theater, order_id)
        logic.emit_event(run_id, order_id, request_id, "ORDER_WORKTREE_READY", {"worktree_path": worktree_path})
        
        # 2.5 Resolve Model Policy
        resolved_model_config = logic.resolve_model_config(
            theater, 
            req.model_profile or req.model or "executor_default", 
            req.model_overrides or {"temperature": req.temperature} if req.temperature is not None else {}
        )

        # 3. Execute Worker
        worker_req = {
            "run_id": run_id,
            "order_id": order_id,
            "attempt": 1,
            "worktree_path": worktree_path,
            "objective": objective,
            "prompt": req.message,
            "prompt_template": req.prompt_template,
            "resolved_model_config": resolved_model_config, # Resolved
            "stall_seconds": req.stall_seconds or STALL_SECONDS,
            "hard_timeout_seconds": req.hard_timeout_seconds or HARD_TIMEOUT,
            "request_id": request_id
        }
        
        worker_res = logic.execute_worker(worker_req)
        
        if worker_res["status"] == "completed":
            order_head = worker_res.get("order_head")
            # 4. Read Artifacts
            answer = logic.read_artifact(worktree_path, "outputs/model_output.txt")
            aar = logic.read_aar(worktree_path)
            
            # 5. Cleanup
            if not keep_wt:
                archive_path = logic.cleanup_vault(theater, order_id)
                logic.emit_event(run_id, order_id, request_id, "ORDER_ARCHIVED", {"archive_path": archive_path})

            logic.emit_event(run_id, order_id, request_id, "ORDER_COMPLETED", {
                "order_head": order_head,
                "worktree_path": worktree_path,
                "artifacts": aar.get("artifacts", []),
                "answer": answer,
                "archive_path": archive_path
            })
            logic.emit_event(run_id, order_id, request_id, "RUN_COMPLETED", {})
            
            return ChatResponse(
                run_id=run_id,
                order_id=order_id,
                status="completed",
                answer=answer,
                worktree_path=worktree_path if keep_wt else None,
                order_head=order_head,
                archive_path=archive_path
            )
        else:
            error = worker_res.get("error", "Worker failed without specific error")
            stage = worker_res.get("stage", "unknown")
            
            logic.emit_event(run_id, order_id, request_id, "ORDER_FAILED", {"error": error, "stage": stage})
            logic.emit_event(run_id, order_id, request_id, "RUN_FAILED", {"error": error})
            
            return ChatResponse(
                run_id=run_id,
                order_id=order_id,
                status="failed",
                error=error
            )
            
    except Exception as e:
        error_msg = str(e)
        logic.emit_event(run_id, order_id, request_id, "ORDER_FAILED", {"error": error_msg, "stage": "orchestration"})
        logic.emit_event(run_id, order_id, request_id, "RUN_FAILED", {"error": error_msg})
        
        return ChatResponse(
            run_id=run_id,
            order_id=order_id,
            status="failed",
            error=error_msg
        )
