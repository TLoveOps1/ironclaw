# IronClaw Vault Service

The Vault service manages the lifecycle of mission workspaces (git worktrees) and ensures archival of state before deletion.

## Core Principles

- **Ephemeral Workspaces**: Worktrees are created for specific orders and removed after use.
- **Archive-First Deletion**: A worktree cannot be removed via the service without first creating a compressed archive (`.tar.gz`) for traceability.
- **Isolation**: Each order operates in its own directory.
- **Path Security**: All operations are restricted to the theater's `worktrees` directory.

## Running Locally

1. Activate venv:
   `source ../../theaters/demo/.venv/bin/activate`
2. Start service:
   `uvicorn main:app --reload --port 8001`

## API Endpoints

- `POST /worktrees`: Create a new git worktree.
- `GET /worktrees/{theater}/{order_id}`: Get worktree status.
- `POST /worktrees/{theater}/{order_id}/archive`: Manually archive a worktree.
- `POST /worktrees/{theater}/{order_id}/remove`: Archive and then remove a worktree.
