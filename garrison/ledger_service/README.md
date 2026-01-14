# IronClaw Ledger Service

The Ledger service manages the append-only record of mission events and provides derived state for mission runs and orders.

## Running Locally

1. Activate venv:
   `source ../../theaters/demo/.venv/bin/activate`
2. Start service:
   `uvicorn main:app --reload --port 8000`
