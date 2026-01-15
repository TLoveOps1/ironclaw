# IronClaw Worker Service

The Worker service is responsible for executing single mission orders inside provisioned workspaces. It is stateless and acts as a "Assault Unit" runner.

## Core Principles

- **Stateless**: The worker preserves no local durable state. Everything is written to the worktree or emitted to the Ledger.
- **Idempotency (Short-Circuit)**: If an `aar.json` with `status: completed` and matching `attempt` already exists in the worktree, the worker skips execution and re-emits the `ORDER_COMPLETED` event only (skipping `ORDER_RUNNING`).
- **Deterministic Order**: The request payload **always overwrites** `order.json` in the worktree, ensuring retries are deterministic according to the latest request.
- **Observable**: Real-time progress is recorded via `outputs/heartbeat.json` inside the worktree.
- **Traceable**: Every lifecycle stage emits an event to the Ledger service, including the specific `stage` of failure.
- **Locked AAR Schema**: The service always writes an `aar.json` following a strict schema (run_id, order_id, attempt, status, stage, model, started_at, ended_at, artifacts, error).

## Configuration (Environment Variables)

- `IRONCLAW_THEATER_ROOT` (Required): The absolute path to the directory containing theater roots and worktrees.
- `LEDGER_URL` (Default: `http://127.0.0.1:8000`): The base URL for the Ledger service.
- `IOINTELLIGENCE_API_KEY` (Required): API key for the model backend.
- `IO_API_BASE_URL` (Default: `https://api.intelligence.io.solutions/api/v1`): The base URL for the model API.

## API Behavior

- **Timeouts**: The service accepts `stall_seconds` (default 300) and `hard_timeout_seconds` (default 900) in the execution request.
- **Failures**: Any uncaught exception during the execution stages results in an `ORDER_FAILED` event being emitted and a valid failure-state `aar.json` being written to the worktree.

## Running Locally

1. Activate venv:
   `source ../../theaters/demo/.venv/bin/activate`
2. Start service:
   `uvicorn main:app --reload --port 8012`

## API Endpoints

- `POST /execute`: Execute an order.
  - Requires `run_id`, `order_id`, `worktree_path`, `objective`, `prompt`, `model`.
  - Returns `status`, `order_head` (commit SHA), or `error`.
- `GET /health`: Basic health check.
