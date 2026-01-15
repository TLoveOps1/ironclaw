from fastapi import FastAPI, HTTPException, BackgroundTasks
from pathlib import Path
import os
import json
import subprocess
import uuid
import requests
from datetime import datetime, timezone
from typing import Optional

from models import ExecutionRequest, ExecutionResponse

app = FastAPI(title="IronClaw Worker Service")

# Configuration
IRONCLAW_THEATER_ROOT = Path(os.environ.get("IRONCLAW_THEATER_ROOT", "/home/tlove96/ironclaw/theaters")).resolve()
LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8000")
IO_API_BASE_URL = os.environ.get("IO_API_BASE_URL", "https://api.intelligence.io.solutions/api/v1")
IOINTELLIGENCE_API_KEY = os.environ.get("IOINTELLIGENCE_API_KEY", "")

@app.get("/health")
async def health():
    return {"status": "ok"}

def validate_worktree_path(path_str: str) -> Path:
    path = Path(path_str).resolve()
    # Must be under {IRONCLAW_THEATER_ROOT}
    if not path.is_relative_to(IRONCLAW_THEATER_ROOT):
        raise HTTPException(status_code=400, detail=f"Invalid worktree path: outside theater root {IRONCLAW_THEATER_ROOT}")
    
    # Must contain .git marker
    if not (path / ".git").exists():
        raise HTTPException(status_code=400, detail="Invalid worktree: no .git marker found")
    
    return path

from runner import WorkerRunner

@app.post("/execute", response_model=ExecutionResponse)
async def execute_order(req: ExecutionRequest):
    wt_path = validate_worktree_path(req.worktree_path)
    
    runner = WorkerRunner(
        ledger_url=LEDGER_URL,
        api_key=IOINTELLIGENCE_API_KEY,
        api_base=IO_API_BASE_URL
    )
    
    result = runner.run(req.dict())
    
    if result["status"] == "failed":
        # We still return 200 but with status="failed" in response body as per IronClaw explicit failure mode
        pass
        
    return ExecutionResponse(
        order_id=req.order_id,
        run_id=req.run_id,
        status=result["status"],
        order_head=result.get("order_head"),
        stage=result.get("stage"),
        error=result.get("error")
    )
