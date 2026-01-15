from pydantic import BaseModel
from typing import Optional

class WorktreeCreate(BaseModel):
    theater: str
    order_id: str
    base_ref: Optional[str] = "master"

class WorktreeResponse(BaseModel):
    order_id: str
    path: str
    exists: bool
    created: bool = False

class ArchiveResponse(BaseModel):
    order_id: str
    archive_path: str
    success: bool
