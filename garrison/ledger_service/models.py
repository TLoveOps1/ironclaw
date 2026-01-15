from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict

class EventCreate(BaseModel):
    event_id: Optional[str] = None
    ts: Optional[str] = None
    run_id: Optional[str] = None
    order_id: Optional[str] = None
    event_type: str
    payload: Dict[str, Any]

class OrderSnapshotModel(BaseModel):
    order_id: str
    run_id: str
    status: str
    ts: str
    worktree: str
    unit_head: str
    order_head: str
    extra: Dict[str, Any]

class RunSnapshotModel(BaseModel):
    run_id: str
    status: str
    message: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    order_ids: List[str]
    max_orders: Optional[int] = None
    worktree: str
    order_head: str
