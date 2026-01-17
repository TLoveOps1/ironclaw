# IronClaw Master Documentation

> **Role**: Master Reference Guide  
> **Scope**: Entire Project  
> **Version**: 1.0 (Generated)

## 1. Project Overview

**IronClaw** is a specialized mission execution and orchestration framework designed for durable, auditable, and resilient AI operations. Unlike typical agent frameworks that rely on fragile in-memory state, IronClaw treats AI execution as **critical infrastructure**.

### Core Philosophy
*   **Execution units are disposable**: Processes can crash or be killed without data loss.
*   **Mission state is permanent**: All state is captured in an immutable append-only ledger.
*   **Isolation by default**: Every mission runs in a pristine, Git-backed worktree.

### How to Read This System
> **Doctrine uses role names** (CO, Assault Unit, Observer) to describe authority and behavior.  
> **Implementation uses service names** (co_service, worker_service, observer_service) to describe code.  
> See [IronClaw_Complete_Spec.md §2](docs/IronClaw_Complete_Spec.md#2-role-taxonomy--watchdog-chain) for the mapping.

---

## 2. Architecture & Services

The system is composed of five distinct microservices (The "Garrison") that work in concert.

| Service | Role | Responsibility |
| :--- | :--- | :--- |
| **Ledger** | Storage | The single source of truth. Append-only event store for all mission states and artifacts. |
| **Vault** | Infrastructure | Manages filesystem lifecycles. Creates, isolates, and archives Git worktrees for missions. |
| **Worker** | Execution | Stateless "Assault Unit". Runs logic, interacts with models, and produces After Action Reports (AARs). |
| **CO** | Orchestration | Command & Oversight. Decomposes missions into orders and dispatches them to workers. |
| **Observer** | Watchdog | Passive monitoring. Detects stalled runs, zombies, and ensures system invariants are met. |

---

## 3. Directory Structure

A complete view of the project layout.

```text
.
├── docs/                               # Comprehensive Documentation & Specs
│   ├── contracts.pdf                   # Formal system contracts
│   ├── index.md                        # Documentation Home
│   ├── IronClaw_Complete_Spec.md       # Authoritative System Specification
│   ├── IronClaw_v1_Design.md           # Architectural Design Document (Historical)
│   ├── IronClaw_v1.md                  # v1 System Specification (Historical)
│   ├── Filesystem_Agent_Playbook.md    # Guide for FS Agent Demo
│   └── _internal/                      # Internal task tracking & TODOs
├── garrison/                           # Source Code for Core Services
│   ├── cli/                            # CLI & Stack Operator
│   │   ├── ironclaw.py                 # Main entrypoint script
│   │   ├── README_STACK.md             # Stack operation guide
│   │   └── README.md
│   ├── co_service/                     # Command & Oversight Service
│   │   ├── logic.py                    # Orchestration logic
│   │   ├── main.py                     # Service entrypoint
│   │   ├── models.py                   # Data models
│   │   └── README.md
│   ├── ledger_service/                 # Ledger Service
│   │   ├── database.py                 # DB interactions
│   │   ├── ingest_jsonl.py             # Data ingestion utilities
│   │   ├── main.py                     # Service entrypoint
│   │   ├── models.py                   # Data models
│   │   └── README.md
│   ├── observer_service/               # Observer Service
│   │   ├── monitor.py                  # Monitoring logic
│   │   ├── main.py                     # Service entrypoint
│   │   ├── signals.py                  # Signal definitions
│   │   └── README.md
│   ├── vault_service/                  # Vault Service
│   │   ├── manager.py                  # Worktree management logic
│   │   ├── main.py                     # Service entrypoint
│   │   ├── models.py                   # Data models
│   │   └── README.md
│   └── worker_service/                 # Worker Service
│       ├── model_io.py                 # LLM Interface
│       ├── runner.py                   # Execution logic
│       ├── main.py                     # Service entrypoint
│       ├── models.py                   # Data models
│       └── README.md
├── theaters/                           # Deployment Configurations
│   └── demo/                           # "Demo" Theater (Local Dev)
│       ├── policy.json                 # Operational policies
│       └── schemas/                    # JSON Schemas for validation
│           ├── aar.schema.json
│           └── order.schema.json
├── tools/                              # Utilities & Tests
│   ├── co_smoke_test.py                # Smoke test for CO service
│   ├── mock_model_server.py            # Mock LLM for offline testing
│   ├── smoke_phaseE_cli.sh             # CLI Integration test
│   ├── smoke_phaseF_observer.sh        # Observer Integration test
│   ├── smoke_phaseG_stack.sh           # Full Stack Integration test
│   ├── smoke_v1_1_model_call.sh        # Model I/O test
│   ├── vault_smoke_test.py             # Vault unit tests
│   └── worker_smoke_test.py            # Worker unit tests
├── LICENSE                             # License File
├── README.md                           # Quickstart README
└── README.old.md                       # Archive of previous README
```

---

## 4. Operational Guide

### Prerequisites
*   Linux Environment (Tested on standard distros)
*   Python 3.8+
*   Git installed and configured

### Quick Start (The "Demo" Theater)

The project includes a `demo` theater configuration for local testing without external infrastructure dependencies.

1.  **Navigate to the CLI**:
    ```bash
    cd garrison/cli
    ```

2.  **Start the Stack**:
    This verifies all services are up and healthy.
    ```bash
    python3 ironclaw.py stack up --theater demo
    ```

3.  **Run a Mission**:
    ```bash
    python3 ironclaw.py chat "Analyze the network logs"
    ```

4.  **View Status**:
    ```bash
    python3 ironclaw.py stack status
    ```

5.  **Shutdown**:
    ```bash
    python3 ironclaw.py stack down
    ```

### Logs & Debugging
The stack operator manages logs centrally.
*   **Tail all logs**: `python3 ironclaw.py stack logs`
*   **Worker specific logs**: `python3 ironclaw.py stack logs worker -f`

State files and logs are typically stored in `~/.ironclaw/stack/`.

---

## 5. Development & Testing

The `tools/` directory contains smoke tests used to verify system integrity during development.

**Key Tests:**
*   `tools/smoke_phaseG_stack.sh`: **The Gold Standard**. Spins up everything and runs a full E2E scenario.
*   `tools/worker_smoke_test.py`: Verifies the worker's ability to process orders in isolation.
*   `tools/mock_model_server.py`: Useful for testing without real LLM API costs.

---

## 6. Documentation Map

Everything you need to know is in `docs/`.

*   **System Specification**: [IronClaw_Complete_Spec.md](docs/IronClaw_Complete_Spec.md) (The comprehensive source of truth).
*   **Design & Architecture**: [IronClaw_v1_Design.md](docs/IronClaw_v1_Design.md) (Architectural reasoning).
*   **Agent Guide**: [Filesystem_Agent_Playbook.md](docs/Filesystem_Agent_Playbook.md) (How to run the FS agent).

---

## 7. Configuration

IronClaw uses Environment Variables and Policy Files.

*   **Global Env**: `IRONCLAW_THEATER` (e.g., "demo")
*   **Service URLs**: `LEDGER_URL`, `VAULT_URL`, etc. (Auto-configured by CLI)
*   **Policy**: Defined in `theaters/<name>/policy.json`. Controls timeouts, retry limits, and allowed models.
