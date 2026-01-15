import os
import subprocess
import tarfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

IRONCLAW_ROOT = Path("/home/tlove96/ironclaw").resolve()
THEATERS_DIR = IRONCLAW_ROOT / "theaters"

class VaultError(Exception):
    pass

def validate_theater(theater: str) -> Path:
    theater_path = (THEATERS_DIR / theater).resolve()
    if not theater_path.is_relative_to(THEATERS_DIR):
        raise VaultError(f"Invalid theater path: {theater}")
    if not theater_path.exists():
        raise VaultError(f"Theater does not exist: {theater}")
    return theater_path

def get_repo_path(theater_path: Path) -> Path:
    repo_path = theater_path / "repo"
    if not repo_path.exists():
        # Fallback to theater root if 'repo' dir doesn't exist (MVP structure varies)
        if (theater_path / ".git").exists():
            return theater_path
        raise VaultError(f"Git repository not found in theater: {theater_path}")
    return repo_path

def create_worktree(theater: str, order_id: str, base_ref: str = "master") -> str:
    theater_path = validate_theater(theater)
    repo_path = get_repo_path(theater_path)
    worktree_path = (theater_path / "worktrees" / order_id).resolve()
    
    if not worktree_path.is_relative_to(theater_path / "worktrees"):
        raise VaultError(f"Invalid worktree path: {order_id}")

    if worktree_path.exists():
        return str(worktree_path), False

    # Ensure worktrees dir exists
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["git", "worktree", "add", "-b", order_id, str(worktree_path), base_ref],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True
        )
        return str(worktree_path), True
    except subprocess.CalledProcessError as e:
        raise VaultError(f"Git worktree creation failed: {e.stderr}")

def get_worktree_status(theater: str, order_id: str) -> Optional[str]:
    theater_path = validate_theater(theater)
    worktree_path = (theater_path / "worktrees" / order_id).resolve()
    if worktree_path.exists() and worktree_path.is_relative_to(theater_path / "worktrees"):
        return str(worktree_path)
    return None

def archive_worktree(theater: str, order_id: str) -> str:
    theater_path = validate_theater(theater)
    worktree_path = (theater_path / "worktrees" / order_id).resolve()
    
    if not worktree_path.exists():
        raise VaultError(f"Worktree does not exist: {order_id}")
    
    archive_dir = theater_path / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archive_name = f"{order_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.tar.gz"
    archive_path = archive_dir / archive_name
    
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(worktree_path, arcname=order_id)
        
    return str(archive_path)

def remove_worktree(theater: str, order_id: str) -> None:
    theater_path = validate_theater(theater)
    repo_path = get_repo_path(theater_path)
    worktree_path = (theater_path / "worktrees" / order_id).resolve()
    
    if not worktree_path.exists():
        return

    # Call git worktree remove
    try:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise VaultError(f"Git worktree removal failed: {e.stderr}")
