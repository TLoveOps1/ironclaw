# IronClaw Stack Operator UX — Phase G

The `ironclaw stack` command provides a single point of control for the IronClaw microservices stack. It orchestrates the starting, stopping, and monitoring of all five core services (Ledger, Vault, Worker, CO, and Observer).

## Core Principles

- **Unified Control**: Start the entire stack with one command (`stack up`).
- **Observability**: Centralized log tailing with service prefixes (`stack logs`).
- **Process Safety**: Atomic state tracking of PIDs and ports to ensure clean shutdowns.
- **Theater Aware**: Configures all services for a specific theater automatically.

## Usage Guide

### 1. Start the Stack
```bash
./ironclaw.py stack up --theater demo
```
This will launch Ledger, Vault, Worker, CO, and Observer in sequence, verifying each is healthy before proceeding to the next.

### 2. Check Status
```bash
./ironclaw.py stack status
```
Displays the PID, port, and health status for each service.

### 3. View Logs
View the last 20 lines of all logs:
```bash
./ironclaw.py stack logs
```
Tail logs for a specific service:
```bash
./ironclaw.py stack logs worker -f
```

### 4. Stop the Stack
```bash
./ironclaw.py stack down
```
Sends a graceful termination signal to all managed processes.

## Configuration

The runner automatically sets the following environment variables for all services:
- `IRONCLAW_THEATER`: Defaults to `demo`.
- `LEDGER_URL`, `VAULT_URL`, `WORKER_URL`, `CO_URL`: Derived from default ports (8010-8013).

## Operator State
- **State File**: `~/.ironclaw/stack/stack_state.json`
- **Logs**: `~/.ironclaw/stack/logs/*.log`
