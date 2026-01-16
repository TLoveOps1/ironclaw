# IronClaw

Live docs: https://tloveops1.github.io/ironclaw/

*IronClaw is a Python-based mission execution and orchestration framework for durable, auditable AI runs in local or self-hosted environments.*

It is built around a simple premise:

> Execution units are disposable.  
> Mission state is permanent.

IronClaw enforces this by combining an append-only event ledger, Git-backed worktrees, and strictly stateless execution units.

---

## Why IronClaw exists

Most AI agent systems fail in predictable ways:

- work is lost on crashes or retries  
- state lives inside process memory or model context  
- failures are opaque and unreplayable  

IronClaw treats AI execution as **infrastructure**, not magic.

Every mission:
- is logged as a sequence of immutable events
- produces filesystem artifacts that can be inspected or replayed
- can be retried safely without duplicating work

This makes failures diagnosable, recoverable, and explainable.

---

## Architecture (high level)

IronClaw is split into five core services, each with a single responsibility:

- **Ledger**  
  Append-only source of truth for all mission and order state.

- **Vault**  
  Owns Git worktree lifecycle, isolation, and archival.

- **Worker**  
  Stateless execution unit. Runs once, writes artifacts and an After Action Report, commits, exits.

- **CO (Command & Oversight)**  
  Central orchestration layer. Plans, dispatches, and synthesizes results.

- **Observer**    
  Passive oversight service. Detects stalled runs, orphaned state, and integrity violations.

Detailed contracts, invariants, and non-goals are documented in the `/docs` directory.

---

## Quick start (demo theater)

Run IronClaw locally using the included demo theater.

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

## Filesystem Agent Demo (Call Summary Mission)

IronClaw includes a working example of a **filesystem-based agent** that follows the
"filesystem + execution" pattern popularized by modern agent runtimes.

### What this demo does

The `filesystem_agent.call_summary` mission demonstrates how IronClaw can:

- plan a mission in the CO (Command & Oversight) service
- provision an isolated worktree via Vault
- materialize inputs and context as files
- execute a mission-specific Worker path
- produce durable, auditable artifacts

Given a short call transcript, the agent:

1. reads the transcript and contextual files from disk
2. calls a language model once to summarize the call
3. extracts action items
4. writes results back to the filesystem

### Worktree layout

For a single mission, the Worker operates inside an isolated worktree:

```text
inputs/
  call.md
  mission.json
context/
  account.json
  playbook.md
outputs/
  summary.md
  action_items.md
  model_output.txt
aar.json
```

- `inputs/` and `context/` are written by the CO service
- `outputs/` and `aar.json` are written by the Worker

### Why this matters

This pattern makes agent behavior:

- **inspectable** (you can open every file)
- **reproducible** (rerun the same worktree)
- **auditable** (AAR records inputs, outputs, and metadata)

The filesystem agent is intentionally simple:

- one mission
- one model call
- no hidden state

More complex agents (multi-step plans, tool loops, retries) can be built on top of the same contract.

### How to run the demo locally

```bash
cd garrison/cli
python3 ironclaw.py stack up
python3 ironclaw.py chat \
  --mission-type filesystem_agent.call_summary \
  --account-name "Acme Corp" \
  --contact-name "Jane Smith" \
  "Jane called about renewal concerns and uptime issues."
```

The Worker will:
1. Read the call transcript from `inputs/call.md`
2. Read account context from `context/account.json`
3. Call the model to generate a summary and action items
4. Write `outputs/summary.md` and `outputs/action_items.md`
5. Commit everything to the worktree and archive it

You can inspect the worktree in `theaters/demo/worktrees/` or the archive in `theaters/demo/archive/`.

---

## Repository structure

```text
ironclaw/
├── README.md              # This file (portfolio overview)
├── docs/                  # Specifications and design docs
├── garrison/              # Core services and CLI
│   ├── cli/               # Human interface and stack control
│   ├── ledger_service/    # Append-only event store
│   ├── vault_service/     # Worktree and artifact management
│   ├── worker_service/    # Stateless execution units
│   ├── co_service/        # Command & Oversight orchestration
│   └── observer_service/  # Passive monitoring and detection
├── theaters/
│   └── demo/              # Demo deployment (no runtime state committed)
└── tools/                 # Smoke tests and verification scripts
```

Runtime state (worktrees, ledgers, archives, secrets) is never committed.

---

## Documentation

For deeper detail:

- **Authoritative system spec**  
  [docs/IronClaw_v1.md](docs/IronClaw_v1.md)

- **Design and architectural rationale**  
  [docs/IronClaw_v1_Design.md](docs/IronClaw_v1_Design.md)

- **CLI and stack operator guide**  
  [garrison/cli/README_STACK.md](garrison/cli/README_STACK.md)

- **Service-level documentation**  
  Individual READMEs under `garrison/`

---

## Project status

- **v1** — Architecturally complete and frozen
- **v1.1** — Hardened execution pipeline and policy-driven control

Future work focuses on:
- richer playbooks and planning
- improved observability
- production-grade deployment profiles

Core guarantees and invariants are intentionally stable.

IronClaw is opinionated by design.

Those opinions are explicit, enforced, and testable.
