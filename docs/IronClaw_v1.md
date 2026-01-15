# IronClaw v1 Specification

## 1) Overview
IronClaw is a microservices-based mission execution and orchestration framework. It provides a robust, idempotent environment for running code associated with missions, ensuring that every operation is logged, verifiable, and protected from redundant execution. By decomposing orchestration (CO), execution (Worker), state management (Ledger), and storage (Vault) into specialized services, IronClaw achieves a high degree of reliability and observability in complex automated workflows.

## 2) Operational Guarantees
IronClaw v1 provides the following authoritative guarantees:

- **Idempotent Execution**: Repeated requests with the same `request_id` do not produce duplicate runs, orders, artifacts, or ledger events. The system short-circuits at the CO, Ledger, and Worker layers.
- **Ledger as Source of Truth**: All mission lifecycle state—including progress, transitions, and outcomes—is derived exclusively from the append-only Ledger event store.
- **Deterministic Identity**: `run_id` and `order_id` are deterministic functions of `request_id`, ensuring consistency across retries and distributed calls.
- **Artifact Integrity**: Successfully completed missions produce a committed Git history, definitive output artifacts (`model_output.txt`), and a standardized After Action Report (`aar.json`).
- **Crash Safety**: System state remains consistent after service failures. Clients can safely retry failed calls; the system will either resume from the last known state or return the cached result.
- **Observable Execution**: All lifecycle transitions (Creation -> Ready -> Running -> Completed/Failed) are captured as discrete events and are externally observable via the Ledger API.
- **Separation of Concerns**: Each service (A-F) has a strictly enforced, single responsibility with no overlapping logic or unauthorized cross-service state mutation.

## 3) Architectural Invariants
The following rules define the "IronClaw-compliant" state for v1:

- **Ledger Invariant**: The Ledger is append-only. Events, once recorded, are never mutated or deleted. Snapshots are ephemeral and fully rebuildable from events.
- **Vault Invariant**: The Vault Service is the sole owner of the Git worktree lifecycle and archival process. No other service may create or delete worktrees directly on disk.
- **Worker Invariant**: The Worker is stateless and ephemeral. It executes logic only within its assigned worktree and communicates outcomes solely through Ledger events and the worktree filesystem.
- **CO Invariant**: The Command & Oversight (CO) service is the exclusive orchestrator of missions. It handles the high-level logic of transitioning missions between Vault and Worker.
- **CLI Invariant**: The CLI is a thin interface. It generates `request_id`s and initiates missions via the CO, but never performs orchestration or execution logic itself.
- **Observer Invariant**: The Observer provides read-only oversight. It detects anomalies (stalls, orphans, integrity gaps) and signals them via the Ledger, but never modifies mission state.
- **Stack Runner Invariant**: The `ironclaw stack` tool is a process manager for operator convenience. It orchestrates service startup/shutdown but does not alter the underlying behavior or logic of the services.

## 4) Explicit Non-Goals
IronClaw v1 does not attempt to provide:

- **Graphical User Interface**: The primary interface is the CLI and JSON over HTTP.
- **Multi-tenant Authentication**: v1 assumes a trusted internal network or single-operator theater.
- **Distributed Consensus**: v1 relies on a central Ledger (SQLite by default) and does not implement Raft/Paxos for the event store.
- **Dynamic Scaling**: Job scheduling and worker pool management are external to the v1 scope.
- **Indefinite Retention**: v1 provides an archival mechanism via Vault, but does not define a long-term data lifecycle or pruning policy.
- **Automatic Self-Healing**: The system detects failures (Observer) and allows safe retries (CO/idempotency), but does not autonomously "fix" broken missions.
- **Autonomous Planning**: v1 executes provided objectives; it does not perform high-level task decomposition or strategy generation.

## 5) Stability & Change Policy
- **Compatibility**: IronClaw v1 guarantees backward compatibility with the declared operational guarantees and invariants.
- **Feature Evolution**: New capabilities will be introduced as explicit, numbered phases (e.g., v1.1, v2.0).
- **Freezing**: Phases A-G are formally frozen. No retroactive modifications to their core logic are permitted within the v1 series.
- **Breaking Changes**: Any violation of v1 invariants or changes to the core event schema requires a major version increment (v2).

## 6) Version Declaration
IronClaw v1 is declared complete and stable as of 2026-01-15.
This specification corresponds to the operational baseline tagged as `phaseG-stack-operator-ux-complete`.
