from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ExecutionRequest(BaseModel):
    run_id: str
    order_id: str
    attempt: int = 1
    worktree_path: str
    
    # Order payload
    objective: str
    prompt: str
    model: str
    temperature: float = 0.2
    
    # Timeouts
    stall_seconds: int = 300
    hard_timeout_seconds: int = 900
    
    # Idempotency
    request_id: Optional[str] = None

class ExecutionResponse(BaseModel):
    order_id: str
    run_id: str
    status: str
    order_head: Optional[str] = None
    stage: Optional[str] = None
    error: Optional[str] = None

class AARModel(BaseModel):
    order_id: str
    run_id: str
    attempt: int
    status: str
    stage: str
    model: Dict[str, Any]
    started_at: str
    ended_at: str
    artifacts: List[Dict[str, Any]] = []
    error: Optional[str] = None
