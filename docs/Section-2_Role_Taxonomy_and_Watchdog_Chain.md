# 2. Role Taxonomy & Watchdog Chain

IronClaw uses a layered command-and-control (C2) hierarchy designed to guarantee mission completion despite unreliable execution units. Oversight is explicit, persistent, and auditable. No unit is trusted indefinitely, including the watchdogs themselves.

The system is organized into **Garrison-level** command roles and **Theater-level** execution roles, connected by a continuous patrol and escalation loop.

---

## 2.1 The Watchdog Chain (System Integrity)

The Watchdog Chain enforces **Asynchronous Command Integrity (ACI)**. Its purpose is to ensure that missions progress even when individual units fail, stall, or disappear. The chain moves from mechanical certainty to intelligent intervention.

### Duty Officer (DO)
* **Role**: Persistent system watchdog.
* **Scope**: Garrison-wide.
* **Responsibilities**:
    * Runs continuous patrol cycles.
    * Scans Orders, queues, and ledgers for stalled progress.
    * Detects unresponsive units or overdue Orders.
    * Reissues Orders or triggers recovery actions.
    * Enforces global budgets and safety constraints.
* **Constraint**: The DO does not perform mission work. It only ensures that work continues.

### Sentinel Unit
* **Role**: Watchdog of the watchdog.
* **Scope**: Garrison-wide, limited authority.
* **Responsibilities**:
    * Verifies that the DO patrol loop is running.
    * Confirms backlog is shrinking or stable.
    * Detects silent failures in oversight logic.
    * Triggers alerts or failover if the DO degrades.
* **Note**: This establishes layered accountability; no single process is implicitly trusted.

### Support Units
* **Role**: Non-AI maintenance executors.
* **Scope**: Garrison-wide.
* **Responsibilities**:
    * Cleanup of expired worktrees.
    * Log compaction and archival.
    * Index rebuilding.
    * Diagnostics and environment repair.
* **Constraint**: Support Units operate on deterministic logic only. They do not reason or make mission decisions.

---

## 2.2 Command Roles (Decision Authority)

### Commanding Officer (CO)
* **Role**: Primary orchestration authority.
* **Scope**: All Theaters.
* **Responsibilities**:
    * Interprets user input.
    * Performs METE planning (Mission Element Task Extraction).
    * Issues Operations and Orders.
    * Assigns Orders to execution units.
    * Synthesizes results into user-facing responses.
* **Interface**: The CO is the only role that directly interfaces with the chat surface. All other roles operate indirectly.

---

## 2.3 Theater-Level Roles (Mission Execution)

Each Theater operates as a semi-autonomous operational zone with its own execution and oversight structure.

### Assault Unit
* **Role**: Ephemeral execution unit.
* **Lifecycle**: Spawn → Execute → Report → Destroy.
* **Responsibilities**:
    * Executes exactly one Order (or bounded sub-chain).
    * Operates in an isolated git worktree.
    * Calls io.intelligence models and approved tools.
    * Writes artifacts and state to disk.
    * Produces an After-Action Report (AAR).
* **Constraints**:
    * No long-term memory.
    * No coordination with other units except via Orders.
    * Never writes directly to Theater mainline state.
    * Assault Units are disposable by design.

### Fireteam
* **Role**: Persistent capability unit.
* **Lifecycle**: Long-lived, resumable.
* **Responsibilities**:
    * Maintains continuity for sustained missions.
    * Holds structured state (not model context).
    * Executes repeated Orders within a domain.
    * Can be re-instantiated with identity intact.
* **Usage**: Used when domain continuity matters, repeated refinement is expected, or short-lived units would thrash context.

### Integration Command
* **Role**: Validation and promotion authority.
* **Scope**: Per-Theater.
* **Responsibilities**:
    * Reviews outputs from Assault Units and Fireteams.
    * Resolves conflicts between parallel efforts.
    * Applies quality gates (tests, checks, policy).
    * Promotes accepted artifacts to Theater mainline state.
* **Constraint**: Integration Command never generates content; it only validates and integrates.

### Observer
* **Role**: Theater-level watchdog.
* **Scope**: Single Theater.
* **Responsibilities**:
    * Monitors unit execution progress.
    * Detects stalled or looping Orders.
    * Verifies clean operational state before cleanup.
    * Escalates failures to the DO or CO when needed.
* **Goal**: Observers ensure Theater activity remains healthy without flooding higher command with noise.

---

## 2.4 Authority Boundaries

IronClaw enforces strict separation of concerns:
* **CO** decides what should happen.
* **Units** execute how it happens.
* **Integration Command** decides what is accepted.
* **Observers / DO** decide when recovery is required.
* **Rule**: No role may silently cross its boundary.

---

## 2.5 Failure Is a First-Class Condition

The role system assumes units will crash, orders may partially complete, artifacts may conflict, and oversight may degrade. The Watchdog Chain exists to ensure failures are detected, state is preserved, work is resumed or reassigned, and missions converge on completion.