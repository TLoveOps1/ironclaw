# IronClaw

*IronClaw is a Python-based mission execution and orchestration framework for durable, auditable AI runs in local or self-hosted environments.*

IronClaw is intended for engineers exploring reliable, self-hosted AI execution systems rather than hosted agent platforms.

It is built around a simple premise:

> **Execution units are disposable.**  
> **Mission state is permanent.**

IronClaw enforces this by combining an append-only event ledger, Git-backed worktrees, and strictly stateless execution units.

---

## Architecture overview

IronClaw follows a **Watchdog Chain** architecture, ensuring every action is recorded, every environment is isolated, and every failure is inspectable.

### System Flow
```mermaid
flowchart TB
    subgraph Client ["Human Interface"]
        CLI["IronClaw CLI<br/>(Chat / Stack Control)"]
    end

    subgraph Garrison ["Garrison (Control Plane)"]
        direction TB
        CO["<b>CO</b><br/>Orchestrator"]
        L[("<b>Ledger</b><br/>Source of Truth")]
        V["<b>Vault</b><br/>Worktree Manager"]
        W["<b>Worker</b><br/>Execution Unit"]
        O["<b>Observer</b><br/>Passive Oversight"]
    end

    subgraph Theater ["Theater (Execution Substrate)"]
        WT[["Git Worktree<br/>(Isolated Context)"]]
        AAR["After Action Report<br/>(aar.json)"]
    end

    CLI -- "chat/mission" --> CO
    CO -- "audit" --> L
    CO -- "provision" --> V
    CO -- "dispatch" --> W

    V -- "manages" --> WT
    W -- "executes in" --> WT
    W -- "writes" --> AAR
    W -- "logs events" --> L

    L -. "monitor" .-> O
    O -. "anomalies" .-> CO

    %% Styling
    style Garrison fill:#f9f9fb,stroke:#d1d5db,stroke-width:2px
    style Theater fill:#f0f9ff,stroke:#bae6fd,stroke-width:2px
    style L fill:#eef2ff,stroke:#4f46e5,stroke-width:2px
    style WT fill:#fff,stroke:#0ea5e9,stroke-width:2px
```

### The Mission Loop (Temporal View)
```mermaid
sequenceDiagram
    autonumber
    participant U as CLI
    participant CO as CO Service
    participant L as Ledger
    participant V as Vault
    participant W as Worker
    
    U->>CO: Submit Mission (request_id)
    CO->>L: Check mission state / Record start
    CO->>V: Request isolated worktree
    V-->>CO: Worktree path
    CO->>W: Dispatch order
    W->>L: Emit heartbeat / Progress
    W->>W: Execute & Generate Artifacts
    W->>L: Emit Completion / AAR Path
    CO-->>U: Return result
```

### Component Reference
| Service | Domain | Responsibility | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Ledger** | Persistence | Append-only event store for mission lifecycle. | SQLite / JSONL |
| **Vault** | Storage | Managing Git worktrees, isolation, and archival. | Filesystem / Git |
| **Worker** | Execution | Stateless mission runner with artifact generation. | AAR (aar.json) |
| **CO** | Orchestration| High-level planning and service dispatch. | Ledger Events |
| **Observer**| Oversight | Monitoring for stalls, orphans, and policy violations. | Signaling Buffer (in-memory / ephemeral)|

---

## Quickstart (demo theater)

Run IronClaw locally using the included demo theater:

```bash
cd garrison/cli
python3 ironclaw.py stack up
python3 ironclaw.py chat "Hello IronClaw"
```

This will:
1. Start the full local service stack
2. Submit a mission
3. Execute it in an isolated Git worktree
4. Persist artifacts and lifecycle events

---

## Learn more

- **Spec** — [IronClaw_v1.md](IronClaw_v1.md)
- **Design deep dive** — [IronClaw_v1_Design.md](IronClaw_v1_Design.md)
- **GitHub repository** — [TLoveOps1/ironclaw](https://github.com/TLoveOps1/ironclaw)
- **Release notes** — [GitHub Release v1.1](https://github.com/TLoveOps1/ironclaw/releases/tag/v1.1)

IronClaw prioritizes correctness, auditability, and operator control over raw throughput or autonomy.
