# IronClaw Ledger Service

The Ledger service manages the append-only record of mission events and provides derived state for mission runs and orders.

## Running Locally

1. Activate venv:
   `source ../../theaters/demo/.venv/bin/activate`
2. Start service:
   `uvicorn main:app --reload --port 8000`

## Idempotency

The `POST /events` endpoint accepts an optional `event_id`. If provided, the service ensures that duplicate events with the same `event_id` are ignored via a `UNIQUE` constraint on the `events` table. If no `event_id` is provided, a UUID is generated.

## Replay and Snapshots

Snapshots are stored in `runs_snapshot` and `orders_snapshot` tables. These are purely derived from the `events` table.
- **Automatic Rebuild**: Currently, the service triggers a full rebuild of snapshots after every `POST /events` to ensure consistency.
- **Manual Rebuild**: Call `POST /rebuild` to force a reconstruction of all snapshots from the canonical event log.
- **Migration**: Use `ingest_jsonl.py` to populate the ledger from existing MVP `.jsonl` files.
