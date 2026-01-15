# IronClaw Worker Service

The Worker service is responsible for executing single mission orders inside provisioned workspaces. It is stateless and acts as a "Assault Unit" runner.

## Core Principles

- **Stateless**: The worker preserves no local durable state. Everything is written to the worktree or emitted to the Ledger.
- **Observable**: Real-time progress is recorded via `heartbeat.json` inside the worktree.
- **Traceable**: Every lifecycle stage emits an event to the Ledger service.
- **Safe**: Restricted to authorized theater roots and cannot mutate git history outside the provided worktree.

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
