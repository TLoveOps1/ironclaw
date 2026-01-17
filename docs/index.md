# IronClaw

*IronClaw is a Python-based mission execution and orchestration framework for durable, auditable AI runs in local or self-hosted environments.*

IronClaw is intended for engineers exploring reliable, self-hosted AI execution systems rather than hosted agent platforms.

<!-- Mermaid support for GitHub Pages -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({ startOnLoad: true });
</script>

It is built around a simple premise:

> **Execution units are disposable.**  
> **Mission state is permanent.**

IronClaw enforces this by combining an append-only event ledger, Git-backed worktrees, and strictly stateless execution units.

---

## Architecture overview

IronClaw follows a **Watchdog Chain** architecture, ensuring every action is recorded, every environment is isolated, and every failure is inspectable.

### System Flow

<div class="mermaid">
flowchart TB
    subgraph Client ["Human Interface"]
        CLI["IronClaw CLI (Chat / Stack Control)"]
    end

    subgraph Garrison ["Garrison (Control Plane)"]
        direction TB
        CO["CO (Orchestrator)"]
        L["Ledger (Source of Truth)"]
        V["Vault (Worktree Manager)"]
        W["Worker (Execution Unit)"]
        O["Observer (Passive Oversight)"]
    end

    subgraph Theater ["Theater (Execution Substrate)"]
        WT["Git Worktree (Isolated Context)"]
        AAR["After Action Report (aar.json)"]
    end

    CLI -- "chat / mission" --> CO
    CO -- "audit" --> L
    CO -- "provision" --> V
    CO -- "dispatch" --> W

    V -- "manages" --> WT
    W -- "executes in" --> WT
    W -- "writes" --> AAR
    W -- "logs events" --> L

    L -. "monitor" .-> O
    O -. "anomalies" .-> CO
</div>

### The Mission Loop (Temporal View)

<div class="mermaid">
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
</div>

### Filesystem Agent Mission Flow

This diagram zooms in on the v1.1 filesystem-based agent, showing how a mission is
materialized, executed, and audited using the filesystem as the primary interface.

<div class="mermaid">
flowchart TD
    User["User / CLI\n(chat or mission request)"]

    subgraph CO["CO Service"]
        COPlan["Plan mission\nmission_type = filesystem_agent.call_summary"]
        COInputs["Write inputs and context\ncall.md, mission.json,\naccount.json, playbook.md"]
    end

    subgraph Vault["Vault Service"]
        VaultWT["Provision isolated Git worktree\n(theater worktree for order)"]
    end

    subgraph Worker["Worker Service\nfilesystem agent path"]
        WRead["Read inputs and context files"]
        WModel["Call model once\n(OpenAI-compatible API / Ollama)"]
        WWrite["Write outputs\nsummary.md, action_items.md,\nmodel_output.txt"]
        WAAR["Update aar.json\nwith mission_type and artifacts"]
    end

    Ledger["Ledger Service\nevents and order snapshot"]

    User --> COPlan
    COPlan --> Ledger
    COPlan --> VaultWT
    VaultWT --> COInputs
    COInputs --> WRead

    WRead --> WModel
    WModel --> WWrite
    WWrite --> WAAR

    WAAR --> Ledger
    WWrite --> User
</div>


### Component Reference

| Service     | Domain          | Responsibility                                              | Source of Truth                     |
|-------------|-----------------|--------------------------------------------------------------|-------------------------------------|
| **Ledger**   | Persistence     | Append-only event store for mission lifecycle                | SQLite / JSONL                      |
| **Vault**    | Storage         | Managing Git worktrees, isolation, and archival               | Filesystem / Git                    |
| **Worker**   | Execution       | Stateless mission runner with artifact generation             | AAR (aar.json)                      |
| **CO**       | Orchestration   | High-level planning and service dispatch                      | Ledger Events                       |
| **Observer** | Oversight       | Monitoring stalls, orphans, and policy violations             | Ephemeral signaling buffer          |

---

## Quickstart (demo theater)

Run IronClaw locally using the included demo theater:

```bash
cd garrison/cli
python3 ironclaw.py stack up
python3 ironclaw.py chat "Hello IronClaw"
```

This will:

- Start the full local service stack
- Submit a mission
- Execute it in an isolated Git worktree
- Persist artifacts and lifecycle events

---

## Releases

IronClaw uses tagged, frozen releases to mark stable milestones.

- **Latest release:**  
  **v1.1.0 — Filesystem Agent Demo**  
  Adds a filesystem-based agent (`filesystem_agent.call_summary`) with durable inputs, outputs, and AARs.  
  [https://github.com/TLoveOps1/ironclaw/releases/tag/v1.1.0](https://github.com/TLoveOps1/ironclaw/releases/tag/v1.1.0)

- **Previous release:**  
  **v1.0.0 — Frozen Core Architecture**  
  Establishes the baseline CO / Vault / Worker / Ledger architecture and execution guarantees.  
  [https://github.com/TLoveOps1/ironclaw/releases/tag/v1.0.0](https://github.com/TLoveOps1/ironclaw/releases/tag/v1.0.0)

**All releases:**  
[https://github.com/TLoveOps1/ironclaw/releases](https://github.com/TLoveOps1/ironclaw/releases)

---

### How to Read This System
> **Doctrine uses role names** (CO, Assault Unit, Observer) to describe authority and behavior.  
> **Implementation uses service names** (co_service, worker_service, observer_service) to describe code.  
> See [IronClaw_Complete_Spec.md §2](IronClaw_Complete_Spec.md#2-role-taxonomy--watchdog-chain) for the mapping.

---

## Learn more

- **System Specification** — [IronClaw_Complete_Spec.md](IronClaw_Complete_Spec.md) (The comprehensive source of truth)
- **Agent Guide** — [Filesystem_Agent_Playbook.md](Filesystem_Agent_Playbook.md)
- **Design deep dive** — [IronClaw_v1_Design.md](IronClaw_v1_Design.md) (Historical context)
- **GitHub repository** — [https://github.com/TLoveOps1/ironclaw](https://github.com/TLoveOps1/ironclaw)
- **Releases** — [https://github.com/TLoveOps1/ironclaw/releases](https://github.com/TLoveOps1/ironclaw/releases)

IronClaw prioritizes correctness, auditability, and operator control over raw throughput or autonomy.
