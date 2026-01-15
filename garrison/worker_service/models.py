from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

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
    status: str
    order_head: Optional[str] = None
    error: Optional[str] = None
