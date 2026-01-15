from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str
    request_id: Optional[str] = None
    theater: Optional[str] = None
    objective: Optional[str] = None
    model: Optional[str] = "executor_default" # Changed default to profile name
    model_profile: Optional[str] = "executor_default"
    model_overrides: Optional[dict] = Field(default_factory=dict)
    prompt_template: Optional[str] = None # Path relative to repo/prompts/
    temperature: Optional[float] = None
    keep_worktree: Optional[bool] = None
    stall_seconds: Optional[int] = None
    hard_timeout_seconds: Optional[int] = None

class WorkerExecutionPayload(BaseModel):
    run_id: str
    order_id: str
    attempt: int
    worktree_path: str
    objective: str
    prompt: str
    resolved_model_config: dict # Renamed from model_config to avoid Pydantic conflict
    prompt_template: Optional[str] = None
    request_id: str
    stall_seconds: int
    hard_timeout_seconds: int

class ChatResponse(BaseModel):
    run_id: str
    order_id: str
    status: str
    answer: Optional[str] = None
    worktree_path: Optional[str] = None
    order_head: Optional[str] = None
    archive_path: Optional[str] = None
    error: Optional[str] = None
