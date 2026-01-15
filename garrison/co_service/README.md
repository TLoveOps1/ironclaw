# IronClaw CO Service (Commanding Officer)

The CO service is the central orchestrator for IronClaw mission runs. It coordinates between the Ledger, Vault, and Worker services to fulfill user chat requests.

## Core Principles

- **Orchestrator**: CO does not execute models or write mission artifacts; it delegates to the Worker and Vault.
- **Idempotent**: Uses `request_id` to derive stable `run_id` and `order_id`. It checks the Ledger first to prevent double-execution.
- **Durable**: Every major orchestration step is recorded as an append-only event in the Ledger.
- **Safe**: Ensures worktrees are archived and removed via Vault after completion unless explicitly kept.

## Configuration (Environment Variables)

- `LEDGER_URL` (Default: `http://127.0.0.1:8010`): The base URL for the Ledger service.
- `VAULT_URL` (Default: `http://127.0.0.1:8011`): The base URL for the Vault service.
- `WORKER_URL` (Default: `http://127.0.0.1:8012`): The base URL for the Worker service.
- `THEATER` (Default: `demo`): The default theater to use for missions.
- `KEEP_WORKTREE` (Default: `false`): If true, worktrees are not archived/removed after completion.
- `WORKER_DEFAULT_STALL_SECONDS` (Default: `300`): Default stall timeout for Worker.
- `WORKER_DEFAULT_HARD_TIMEOUT_SECONDS` (Default: `900`): Default hard timeout for Worker.

## API Behavior

- **Idempotency**: The service checks the Ledger for an existing `completed` snapshot before starting orchestration. If found, it returns the cached `answer` and `order_head` immediately.
- **Timeouts**: `stall_seconds` and `hard_timeout_seconds` can be specified per-request; otherwise, defaults from env are forwarded to the Worker.
- **Cleanup**: Unless `keep_worktree` is true (via env or request), the worktree is archived and removed via Vault, and the `archive_path` is recorded in the Ledger.

## Running Locally

1. Activate venv:
   `source ../../theaters/demo/.venv/bin/activate`
2. Start service:
   `uvicorn main:app --reload --port 8013`

## API Endpoints

- `POST /chat`: Orchestrate a mission run.
  - Accepts `message`, `request_id`, `theater`, `model`, `temperature`, `keep_worktree`.
  - Returns `run_id`, `order_id`, `status`, `answer`, `archive_path`.
- `GET /health`: Basic health check.
