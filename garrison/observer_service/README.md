# IronClaw Observer Service (Theater Oversight)

The Observer Service provides persistent oversight for a specific theater, detecting stalled missions, orphan worktrees, and integrity failures.

## Core Principles

- **Oversight Only**: Observer detects and alerts, but never executes missions or modifications.
- **Read-Only Inspection**: Inspects worktrees and Ledger events without altering mission state.
- **Delegated Action**: If configured, triggers cleanup via Vault's existing endpoints.
- **Deduplicated Signaling**: Prevents spam by deduping alerts for the same condition.

## Configuration (Environment Variables)

| Variable | Description | Default |
|----------|-------------|---------|
| `IRONCLAW_THEATER` | ID of the theater to oversee | `demo` |
| `IRONCLAW_LEDGER_URL` | Base URL for the Ledger | `http://127.0.0.1:8010` |
| `IRONCLAW_VAULT_URL` | Base URL for the Vault | `http://127.0.0.1:8011` |
| `STALL_SECONDS` | Inactivity threshold for stalls | `1800` (30m) |
| `MAX_WALL_SECONDS` | Absolute wall-clock cap for missions | `3600` (1h) |
| `ORPHAN_TTL_SECONDS` | Threshold for calling terminal worktrees orphans | `3600` (1h) |
| `POLL_INTERVAL_SECONDS` | How often the monitor loop runs | `30` |
| `ENABLE_VAULT_CLEANUP` | Whether to trigger Vault removal for orphans | `false` |

## Endpoints

- `GET /healthz`: Health and configuration check.
- `GET /status`: Monitoring statistics (poll count, detections).
- `GET /alerts`: Currently active, deduped alerts.

## Running Locally

1. Activate venv:
   `source ../../theaters/demo/.venv/bin/activate`
2. Start service:
   `uvicorn main:app --reload --port 8014`

## Escalation

Alerts are emitted as `observer.*` events to the Ledger and appended to the local audit log:
`~/.ironclaw/observer/alerts.jsonl`
