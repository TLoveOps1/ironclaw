# IronClaw Worker Service

The Worker service is responsible for executing single mission orders inside provisioned workspaces. It is stateless and acts as a "Assault Unit" runner.

## Core Principles

- **Stateless**: The worker preserves no local durable state. Everything is written to the worktree or emitted to the Ledger.
- **Idempotency (Short-Circuit)**: If an `aar.json` with `status: completed` and matching `attempt` already exists in the worktree, the worker skips execution and re-emits the completion event.
- **Deterministic Order**: The request payload **always overwrites** `order.json` in the worktree, ensuring retries are deterministic according to the latest request.
- **Observable**: Real-time progress is recorded via `heartbeat.json` inside the worktree.
- **Traceable**: Every lifecycle stage emits an event to the Ledger service, including the specific `stage` of failure.
- **Locked AAR Schema**: The service always writes an `aar.json` following a strict schema (run_id, order_id, attempt, status, stage, model, started_at, ended_at, artifacts, error).

## Running Locally

1. Activate venv:
   `source ../../theaters/demo/.venv/bin/activate`
2. Set environment:
   `export LEDGER_URL=http://127.0.0.1:8000`
   `export IOINTELLIGENCE_API_KEY=your_key`
3. Start service:
   `uvicorn main:app --reload --port 8012`

## API Endpoints

- `POST /execute`: Execute an order.
  - Requires `run_id`, `order_id`, `worktree_path`, `objective`, `prompt`, `model`.
  - Returns `status`, `order_head` (commit SHA), or `error`.
- `GET /health`: Basic health check.
