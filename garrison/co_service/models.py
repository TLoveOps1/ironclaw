from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str
    request_id: Optional[str] = None
    theater: Optional[str] = None
    objective: Optional[str] = None
    model: Optional[str] = "meta-llama/Llama-3.3-70B-Instruct"
    temperature: Optional[float] = 0.2
    keep_worktree: Optional[bool] = None
    stall_seconds: Optional[int] = None
    hard_timeout_seconds: Optional[int] = None

class ChatResponse(BaseModel):
    run_id: str
    order_id: str
    status: str
    answer: Optional[str] = None
    worktree_path: Optional[str] = None
    order_head: Optional[str] = None
    archive_path: Optional[str] = None
    error: Optional[str] = None
