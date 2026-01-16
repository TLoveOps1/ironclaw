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
    prompt_template: Optional[str] = None
    resolved_model_config: Dict[str, Any]
    
    # Timeouts
    stall_seconds: int = 300
    hard_timeout_seconds: int = 900
    
    # Idempotency
    request_id: Optional[str] = None
    
    # Mission Context
    mission_type: str = "default"

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
    started_at: str
    ended_at: str
    model_profile: str
    model_id: str
    prompt_template_path: Optional[str] = None
    prompt_template_commit_sha: Optional[str] = None
    prompt_hash: str
    response_hash: str
    cache_hit: bool
    latency_ms: float
    usage: Dict[str, Any]
    artifacts: List[Dict[str, Any]] = []
    error: Optional[str] = None
