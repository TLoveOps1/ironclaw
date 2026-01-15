from fastapi import FastAPI, HTTPException
from models import WorktreeCreate, WorktreeResponse, ArchiveResponse
import manager

app = FastAPI(title="IronClaw Vault Service")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/worktrees", response_model=WorktreeResponse)
async def create_worktree(req: WorktreeCreate):
    try:
        path, created = manager.create_worktree(req.theater, req.order_id, req.base_ref)
        return WorktreeResponse(order_id=req.order_id, path=path, exists=True, created=created)
    except manager.VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/worktrees/{theater}/{order_id}", response_model=WorktreeResponse)
async def get_worktree(theater: str, order_id: str):
    try:
        path = manager.get_worktree_status(theater, order_id)
        if path:
            return WorktreeResponse(order_id=order_id, path=path, exists=True)
        return WorktreeResponse(order_id=order_id, path="", exists=False)
    except manager.VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/worktrees/{theater}/{order_id}/archive", response_model=ArchiveResponse)
async def archive_worktree(theater: str, order_id: str):
    try:
        archive_path = manager.archive_worktree(theater, order_id)
        return ArchiveResponse(order_id=order_id, archive_path=archive_path, success=True)
    except manager.VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/worktrees/{theater}/{order_id}/remove")
async def remove_worktree(theater: str, order_id: str):
    try:
        # IronClaw invariant: archive-first
        print(f"Archiving {order_id} before removal...")
        archive_path = manager.archive_worktree(theater, order_id)
        print(f"Archive created at {archive_path}")
        manager.remove_worktree(theater, order_id)
        return {"status": "removed", "archive_path": archive_path}
    except manager.VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))
