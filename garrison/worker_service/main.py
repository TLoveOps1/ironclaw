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

@app.post("/execute", response_model=ExecutionResponse)
async def execute_order(req: ExecutionRequest):
    # This will be implemented in the next step
    wt_path = validate_worktree_path(req.worktree_path)
    return ExecutionResponse(order_id=req.order_id, status="accepted")
