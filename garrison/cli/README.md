# IronClaw CLI — Phase E

The `ironclaw` CLI is the primary human interface to the IronClaw system. It acts as a thin client over the CO (Commanding Officer) service, providing developer ergonomics such as `request_id` persistence and safe retries.

## Core Principles

- **Thin Client**: The CLI does not orchestrate; it only calls the CO service.
- **Safe Retries**: Uses a locally persisted `request_id` to ensure that retrying a failed or timed-out request is idempotent.
- **Observable**: Provides structured, human-readable output by default, with raw JSON support for scripts.

## Setup

1. Ensure Python 3 and `requests` are installed.
2. The CLI is located at `garrison/cli/ironclaw.py`.
3. (Optional) Alias it for convenience:
   `alias ironclaw='python3 /home/tlove96/ironclaw/garrison/cli/ironclaw.py'`

## Usage Examples

### 1. Send a Chat Request
```bash
./ironclaw.py chat "Say 'IronClaw' and nothing else."
```

### 2. Retry the Last Request
If a request fails or you want to ensure it was processed:
```bash
./ironclaw.py chat --retry
```
This re-sends the exact same payload and `request_id` as the previous attempt.

### 3. Force a New Request
Even if local state exists, force a new `request_id`:
```bash
./ironclaw.py chat "Another mission." --new
```

### 4. Machine Readable Output
```bash
./ironclaw.py chat "Status check." --json
```

## Configuration (Environment Variables)

- `IRONCLAW_CO_URL`: The base URL for the CO service (default: `http://127.0.0.1:8013`).

## Local State

The CLI persists its local state in `~/.ironclaw/client/`:
- `last_request.json`: Stores the details of the most recent request for use with `--retry`.
- `history.jsonl`: A local audit log of CLI invocations.
