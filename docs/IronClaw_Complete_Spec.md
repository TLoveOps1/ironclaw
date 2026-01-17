# IronClaw: Complete System Specification

*A comprehensive guide to the IronClaw mission execution and orchestration framework*


---

## Table of Contents

1. [Overview & Vision](#1-overview--vision)
2. [Role Taxonomy & Watchdog Chain](#2-role-taxonomy--watchdog-chain)
3. [Detailed Unit Constraints](#3-detailed-unit-constraints--assault-units--observers)
4. [The Interaction Loop](#4-the-interaction-loop-intent-to-integration)
5. [Mission Planning & METE](#5-mission-planning--mete)
6. [Unit Lifecycle & Decommissioning](#6-unit-lifecycle--decommissioning)
7. [Configuration & State](#7-configuration--state)
8. [Extensibility & Playbooks](#8-extensibility--playbooks)
9. [The Operational Ledger & Artifact Management](#9-the-operational-ledger--artifact-management)
10. [Glossary & Operational Guarantees](#10-glossary--operational-guarantees)

---

## 1. Overview & Vision

IronClaw is an **agentic command-and-control (C2) environment** built to power a general-purpose conversational system. It autonomously plans, executes, and completes complex missions using ephemeral AI units while persisting all meaningful state outside the model.

IronClaw is not an IDE tool or developer assistant; it is a **mission execution system** that presents itself through a chat interface.

### Core Functionality

Behind its single conversational interface, IronClaw performs several critical functions:
* **Decomposes** user intent into atomic, auditable tasks.
* **Dispatches** short-lived execution units.
* **Persists** all work in git-backed operational directories.
* **Validates** and integrates results.
* **Learns** over time through durable policy and outcome tracking.

> **Core Philosophy:** All AI units are disposable. All mission state is permanent.

### The Core Problem vs. IronClaw's Solution

Modern agent systems often fail because they lose context, coordination is manual, and "learning" is trapped inside volatile model memory. IronClaw treats these failures as expected conditions rather than edge cases.

| Challenge | IronClaw Approach |
| :--- | :--- |
| **Agent context loss** | All work state is persisted in git-backed operational artifacts. |
| **Unreliable execution** | Orders are durable; failed units are replaced. |
| **Manual coordination** | C2 structure with explicit tasking. |
| **Scaling agents** | Ephemeral units + strict lifecycles. |
| **Hidden failure** | Event logs + After-Action Reports. |
| **Vanishing "Learning"** | Policy updates driven by outcomes, not memory. |

### Design Goals & Principles

IronClaw is built on the following non-negotiable principles:
* **Durability First:** No meaningful work lives only in model context.
* **Ephemeral Execution:** Units exist only to complete Orders, then are destroyed.
* **Explicit Control Flow:** Every action is traceable to an Order, Task Chain, or Playbook.
* **Asynchronous Integrity:** The system converges on success even when individual steps fail.
* **Chat as Interface:** Conversation is the input/output layer—not the control plane.

### Technology Foundation

Implemented primarily in **Python**, the system utilizes a distributed-system architecture:
* **io.intelligence:** The model execution backend (OpenAI-compatible API).
* **Git Repositories + Worktrees:** Used for durable operational state.
* **Structured Ledgers:** Records for events, Orders, and outcomes.
* **Queue-based Execution:** Enables scalable, asynchronous unit dispatch.

### Mental Model: The Operational Flow

IronClaw is a mission system that "speaks" chat. Its operational flow follows a strict progression:
**Intent** → **Orders** → **Execution Units** → **Persistent Artifacts** → **Validation** → **Response** → **Policy Update**.

---

## 2. Role Taxonomy & Watchdog Chain

IronClaw uses a layered command-and-control (C2) hierarchy designed to guarantee mission completion despite unreliable execution units. Oversight is explicit, persistent, and auditable. No unit is trusted indefinitely, including the watchdogs themselves.

The system is organized into **Garrison-level** command roles and **Theater-level** execution roles, connected by a continuous patrol and escalation loop.

### The Watchdog Chain (System Integrity)

The Watchdog Chain enforces **Asynchronous Command Integrity (ACI)**. Its purpose is to ensure that missions progress even when individual units fail, stall, or disappear.

**Duty Officer (DO)**
* **Role**: Persistent system watchdog.
* **Scope**: Garrison-wide.
* **Responsibilities**: Runs continuous patrol cycles, scans Orders/queues/ledgers for stalled progress, detects unresponsive units, reissues Orders, enforces global budgets and safety constraints.
* **Constraint**: The DO does not perform mission work. It only ensures that work continues.

**Sentinel Unit**
* **Role**: Watchdog of the watchdog.
* **Scope**: Garrison-wide, limited authority.
* **Responsibilities**: Verifies DO patrol loop is running, confirms backlog is shrinking or stable, detects silent failures in oversight logic, triggers alerts or failover if DO degrades.

**Support Units**
* **Role**: Non-AI maintenance executors.
* **Responsibilities**: Cleanup of expired worktrees, log compaction and archival, index rebuilding, diagnostics and environment repair.
* **Constraint**: Support Units operate on deterministic logic only. They do not reason or make mission decisions.

### Command Roles (Decision Authority)

**Commanding Officer (CO)**
* **Role**: Primary orchestration authority.
* **Scope**: All Theaters.
* **Responsibilities**: Interprets user input, performs METE planning, issues Operations and Orders, assigns Orders to execution units, synthesizes results into user-facing responses.
* **Interface**: The CO is the only role that directly interfaces with the chat surface.

### Theater-Level Roles (Mission Execution)

**Assault Unit**
* **Role**: Ephemeral execution unit.
* **Lifecycle**: Spawn → Execute → Report → Destroy.
* **Responsibilities**: Executes exactly one Order, operates in isolated git worktree, calls io.intelligence models and approved tools, writes artifacts and state to disk, produces After-Action Report (AAR).
* **Constraints**: No long-term memory, no coordination with other units except via Orders, never writes directly to Theater mainline state.

**Fireteam**
* **Role**: Persistent capability unit.
* **Lifecycle**: Long-lived, resumable.
* **Responsibilities**: Maintains continuity for sustained missions, holds structured state (not model context), executes repeated Orders within a domain.
* **Usage**: Used when domain continuity matters or short-lived units would thrash context.

**Integration Command**
* **Role**: Validation and promotion authority.
* **Scope**: Per-Theater.
* **Responsibilities**: Reviews outputs from units, resolves conflicts between parallel efforts, applies quality gates, promotes accepted artifacts to Theater mainline state.
* **Constraint**: Integration Command never generates content; it only validates and integrates.

**Observer**
* **Role**: Theater-level watchdog.
* **Scope**: Single Theater.
* **Responsibilities**: Monitors unit execution progress, detects stalled or looping Orders, verifies clean operational state, escalates failures to DO or CO when needed.

### Authority Boundaries

IronClaw enforces strict separation of concerns:
* **CO** decides what should happen.
* **Units** execute how it happens.
* **Integration Command** decides what is accepted.
* **Observers / DO** decide when recovery is required.
* **Rule**: No role may silently cross its boundary.

### Failure Is a First-Class Condition

The role system assumes units will crash, orders may partially complete, artifacts may conflict, and oversight may degrade. The Watchdog Chain exists to ensure failures are detected, state is preserved, work is resumed or reassigned, and missions converge on completion.

---

## 3. Detailed Unit Constraints — Assault Units & Observers

This section defines hard operational constraints for Theater-level units. These constraints are non-negotiable and exist to preserve system stability, auditability, and mission convergence.

### Assault Unit (Primary Executor)

**Core Constraints**

1. **Single-Order Focus**: An Assault Unit may execute only one Order at a time. It must not poll for additional Orders or observe other units.

2. **Directory Containment**: Each Assault Unit is confined to its assigned operational worktree: `theaters/<theater>/worktrees/order_<order_id>/`. No filesystem access is permitted outside this boundary.

3. **Execution Propulsion**: Assault Units must always advance the Order state forward. They must write intermediate state to disk and emit ledger events for each meaningful step. Stalling is considered a fault condition.

4. **Self-Termination & Handoff**: Assault Units are responsible for initiating their own shutdown when context fills, logical work boundaries are reached, or the Order is complete/irrecoverable.

5. **Git Discipline**: Units work only on their isolated worktree and commit all outputs locally. They never merge or push to Theater mainline. All promotion authority belongs to Integration Command.

**Allowed Capabilities**
* **May**: Call io.intelligence models using approved profiles, run allowed local tools, read referenced artifacts, write structured outputs/reports.
* **May Not**: Modify policies, spawn other units, alter Orders, or bypass Integration Command.

### Observer (Theater Oversight Unit)

**Core Constraints**

1. **Oversight Only**: Observers are strictly prohibited from implementing changes, writing artifacts, or generating mission outputs. Their authority is diagnostic and supervisory only.

2. **Lifecycle Ownership**: Observers own the execution lifecycle within a Theater. They track unit start/completion and verify clean operational state. No unit may be destroyed without Observer verification.

3. **Stall Detection**: Observers continuously monitor for lack of ledger progress, no filesystem changes, exceeded budgets, or repeated retries without progress.

4. **Communication Discipline**: Observers must communicate sparingly and intentionally. They notify higher command only for recovery-required conditions, repeated failures, policy violations, or integrity risks.

5. **Integration Coordination**: Observers act as the bridge to Integration Command. They validate that outputs are complete and artifacts are committed.

### Prohibited Behaviors (All Units)

The following behaviors are explicitly forbidden:
* Passive waiting without emitting state.
* Silent failure.
* Modifying Orders in-place.
* Cross-unit coordination outside Orders.
* Retaining uncommitted work at shutdown.
* Implicit authority escalation.

### Why These Constraints Exist

These constraints ensure execution remains auditable, failures are recoverable, concurrency is manageable, and scaling does not create chaos. Learning is based on outcomes rather than hidden reasoning.

---

## 4. The Interaction Loop: Intent to Integration

IronClaw follows a rigid, linear progression for every user interaction. This ensures that no request is "lost" in conversation and that every output is the result of a structured mission.

### Phase 1: Intent & Planning (Commanding Officer)

The loop begins when a user provides input via the chat interface.
1. **Intent Extraction**: The CO analyzes the input to determine the objective.
2. **METE Planning**: The CO performs **Mission Element Task Extraction**. It breaks the high-level intent into specific Operations and individual Orders.
3. **The Theater Blueprint**: The CO selects or generates a **Playbook** (a reusable sequence of steps) or a **Task Chain** (a dynamic sequence for novel tasks).

### Phase 2: Dispatch (The Ledger)

Once the plan is set, the CO does not "do" the work. It "orders" it.
1. **Order Issuance**: The CO writes structured Orders into the **Orders Ledger**.
2. **Unit Spawning**: The system instantiates the necessary **Assault Units** or **Fireteams**.
3. **Queue Assignment**: Orders are pinned to the **Orders Queue**. The presence of an Order in this queue is a directive for the unit to begin execution immediately.

### Phase 3: Execution (Theater Units)

This is where the actual labor occurs in isolation.
1. **Worktree Initialization**: The unit is given a fresh git worktree.
2. **Tool Use**: The unit utilizes io.intelligence and local tools to perform the task.
3. **Progress Signals**: As the unit works, it emits **Signals** to the ledger so the Observer and DO can track health.
4. **Completion**: The unit writes its final changes to its local worktree and generates an **After-Action Report (AAR)**.

### Phase 4: Oversight & Recovery (The Watchdog)

While execution is happening, the Watchdog Chain is active.
1. **Patrol**: The **Observer** or **Duty Officer** scans the ledger.
2. **Health Check**: If a unit is stalled or failing, the Watchdog intervenes (retries, reassigns, or escalates).
3. **Integrity Check**: Once a unit claims completion, the Watchdog verifies the artifacts exist on disk before allowing the unit to terminate.

### Phase 5: Integration & Promotion (Integration Command)

Work done in a worktree is not yet part of the "official" project state.
1. **Validation**: **Integration Command** runs tests, linters, or policy checks against the unit's worktree.
2. **Conflict Resolution**: If multiple units were working on related files, Integration Command merges the changes.
3. **Promotion**: Validated work is committed to the Theater mainline state.

### Phase 6: Synthesis & Learning (CO & Policy)

The loop closes back at the command level.
1. **Outcome Review**: The CO reviews the AARs and the integrated state.
2. **Response**: The CO provides a final update to the user via the chat interface.
3. **Policy Update**: If the mission revealed a better way to handle a task, the **Policy** is updated so the system "learns" for future missions.

### Summary of the Loop

**User Input** → **Plan** → **Order** → **Execute** → **Verify** → **Integrate** → **Report**

---

## 5. Mission Planning & METE

Mission planning is the process of converting ambiguous user intent into a high-precision execution roadmap. IronClaw uses a framework called **METE** to ensure that planning is structured, repeatable, and decoupled from the execution phase.

### The METE Framework

METE stands for **Mission Element Task Extraction**. It is the formal logic used by the Commanding Officer (CO) to translate a request into actionable work.

1. **Mission (The Goal)**: The overarching objective defined by the user.
2. **Elements (The Components)**: The logical blocks required to complete the mission.
3. **Tasks (The Actions)**: The atomic steps within each element.
4. **Extraction (The Output)**: The process of packaging these tasks into structured **Orders**.

### The Planning Process

**1. Situation Assessment**: The CO scans the current environment, existing files, and relevant policy documents to understand the context of the request.

**2. Strategy Selection**: The CO decides how to approach the problem:
* **Playbook Path**: If the mission matches a known pattern, the CO uses a predefined Playbook.
* **Task Chain Path**: If the mission is novel, the CO generates a dynamic chain of dependent tasks.

**3. Dependency Mapping**: The CO identifies which tasks must happen sequentially and which can happen in parallel.

**4. Operational Budgeting**: The CO assigns a "budget" to the mission, including time limits (TTL) for each order, retry limits for failures, and tool access level for the units.

### Output: The Order Packet

The result of METE is a set of **Order Packets**. Every packet contains:
* **Objective**: A concise description of the desired outcome.
* **Reference Material**: Links to existing code, documentation, or previous AARs.
* **Rules of Engagement (ROE)**: Specific constraints the unit must follow.
* **Success Criteria**: How the unit (and the Integration Command) will know the task is finished.

### Dynamic Re-Planning

Planning does not end when execution starts. IronClaw supports **asynchronous refinement**:
* If an Assault Unit discovers a blocker, it records this in its AAR.
* The CO receives the report, adjusts the mission plan, and issues new Orders to resolve the blocker.
* This creates a "self-correcting" planning loop that can handle surprises without human intervention.

### Why METE?

By forcing the CO to extract tasks into a formal structure, IronClaw avoids the "black box" problem of typical AI agents. You can see exactly what the system planned to do *before* it starts doing it.

---

## 6. Unit Lifecycle & Decommissioning

IronClaw treats execution units as consumable instruments, not long-lived actors. Units exist solely to execute Orders and must leave the system in a known, verifiable state when finished.

### Unit Lifecycle States

All execution units progress through a strict lifecycle:

* **Spawned**: The unit process/container is created. Identity and scope are assigned.
* **Active**: The unit has claimed an Order. An operational worktree is created, and execution begins immediately.
* **Blocked**: The unit encounters an external dependency or constraint. The blockage is recorded with reason and context.
* **Completed**: Order objectives are met. Artifacts are written and committed, and an AAR is produced.
* **Failed**: The Order cannot be completed within constraints. Failure is explicit and documented.
* **Decommissioned**: The unit exits cleanly. No further execution occurs, and cleanup is authorized.

### Clean Shutdown Requirements

Before decommissioning, a unit must satisfy all of the following conditions:
1. All artifacts are written to disk.
2. The Git worktree is in a consistent state.
3. The After-Action Report (AAR) is complete.
4. Ledger events are flushed.
5. No untracked or dangling state remains.

**Note:** Failure to meet these conditions triggers recovery processes rather than destruction.

### Decommissioning Authority

Units may not self-destruct arbitrarily:
* **Assault Units**: May request decommissioning after completion or failure. The Observer must verify the state before approval.
* **Fireteams**: Decommissioned only by explicit command. Persistent state must be preserved.
* **Observers**: Authorize unit teardown after verification.
* **Duty Officer**: May forcibly terminate units during recovery but must preserve all reachable state.

### Forced Termination (Recovery Mode)

Forced termination occurs only when a unit is unresponsive or violating constraints:
1. **Snapshot**: The system snapshots the current filesystem state.
2. **Record**: The termination reason is recorded in the ledger.
3. **Terminate**: The process or container is terminated.
4. **Reissue**: The Order is reissued to a fresh unit.

### Orphan Detection

IronClaw actively scans for orphaned execution state, including worktrees with no active unit, units with no ledger heartbeat, and Orders marked active with no progress. Orphans are quarantined, inspected, and either resumed by a new unit or archived as failed attempts.

### Why This Lifecycle Exists

This lifecycle guarantees predictable system behavior, recoverable failures, bounded resource usage, clean scaling across many units, and detailed post-mortem analysis for every single failure.

---

## 7. Configuration & State

IronClaw separates configuration, operational state, and historical record. Each has a distinct storage model and lifecycle to ensure reliability, auditability, and controlled evolution over time.

### Configuration Layers (Override Hierarchy)

Configuration is resolved through a strict precedence order:

1. **System Defaults (Lowest Priority)**: Hardcoded safe fallbacks with minimal assumptions.
2. **Garrison Configuration**: Global policies, limits, model profiles, io.intelligence routing, and default Playbooks. *Location:* `garrison/config/`
3. **Theater Configuration**: Mission- or project-specific overrides, tool allowlists, budget adjustments, and integration rules. *Location:* `theaters/<theater>/config/`
4. **Run-Level Overrides (Highest Priority)**: Temporary constraints for a specific mission. These are explicitly scoped and non-persistent.

**Rule:** Configuration is never modified by execution units.

### Model & Tool Profiles (io.intelligence)

IronClaw treats models as interchangeable execution resources selected by policy rather than hardcoding. Profiles define model identifier, temperature and sampling parameters, cost and latency expectations, and allowed task types.

Routing policies determine which profile is used for each Order type, enabling model swapping without refactors and cost-aware execution.

### Operational State

Operational state represents what is happening "now." It is stored as structured records in the ledger, minimal filesystem markers, and derived views.
* **Examples:** Active Orders, unit status, retry counts, and escalation flags.
* **Characteristics:** Mutable, queryable, and derived from events where possible.

### Events as Data (Immutable History)

All significant actions emit events. Events are the ground truth of the system.
* **Properties:** Append-only, timestamped, linked (to Run, Order, and unit), and never modified or deleted.
* **Records:** Task assignment, execution start/stop, failures, retries, integration decisions, and escalations.

### Derived State (Snapshots)

To avoid replaying the entire event log for every query, IronClaw maintains versioned snapshots.
* Snapshots are treated as cache, not truth.
* If a snapshot is lost, it is regenerated from the event log.

### Labels as State

Fast-changing conditions are tracked using lightweight labels (e.g., `mode.degraded`, `order.blocked.external`). These support fast queries and are always backed by events.

### State Recovery

IronClaw assumes state corruption and interruption are possible. Recovery guarantees ensure events are replayable, snapshots are regenerable, worktrees preserve partial outputs, Orders can be reissued safely, and no single store is a single point of failure.

### Why This Separation Matters

This model ensures configuration changes are deliberate, execution cannot mutate policy, history is never lost, live state is inspectable, and learning and adaptation are explainable.

### io.intelligence Integration Model

IronClaw does not delegate control, memory, or coordination to io.intelligence; it is treated as stateless execution infrastructure.

| Aspect | IronClaw Unit | io.intelligence |
| :--- | :--- | :--- |
| **Lifecycle** | Spawn → Execute → Report → Destroy | Per-request only |
| **Identity** | Unit ID | API key + model |
| **Memory** | Files + ledger | None |
| **State** | Durable | Stateless |
| **Failure Handling** | Reissue Order | Retry request |
| **Auditability** | Full | Request/response only |

**Design Guarantee:** Because state is infrastructure rather than residing in a model, IronClaw can delete every unit at any time, restart the system, and still converge on mission completion.

---

## 8. Extensibility & Playbooks

IronClaw is designed to be extended without modifying the core command-and-control logic. This is achieved through **Playbooks** and **Tool Definition**.

### Playbooks: Predefined Mission Logic

A Playbook is a structured template for common missions. Instead of the CO "guessing" how to handle a request, it retrieves the appropriate Playbook to ensure consistency.

* **Structure**: Playbooks define a sequence of Operations, required unit roles, and specific success criteria.
* **Version Control**: Playbooks are stored in the Garrison repository and are versioned like code.
* **Customization**: While the structure is fixed, the CO can inject mission-specific variables into the Playbook at runtime.

**Example Playbook Categories:**
* **Feature-Branch**: Planning, coding, testing, and PR creation.
* **Infrastructure-Audit**: Security scanning, dependency checks, and reporting.
* **Research-Deep-Dive**: Web search, document synthesis, and bibliography generation.

### Task Chains: Dynamic Execution

For novel requests that do not fit a Playbook, the CO generates a **Task Chain**.
* **Linear & Branching**: Tasks can be strictly sequential or branch out into parallel work.
* **State Propagation**: Outputs from one task in the chain are automatically passed as inputs (Federated References) to the next.
* **Evaluation**: The CO evaluates the progress of the chain after each major milestone.

### Rules of Engagement (ROE)

Extensibility is governed by ROE:
* **ROE-EXEC**: Units must always advance the state; stalling is a failure.
* **ROE-ISOLATE**: All work must happen in a dedicated worktree.
* **ROE-REPORT**: No task is complete until an After-Action Report is written.

### Custom Tool Integration

New capabilities are added to IronClaw via **Tool Profiles**:
1. **Definition**: Define the tool's input/output schema (compatible with io.intelligence).
2. **Permissions**: Assign the tool to specific roles.
3. **Logging**: Every tool call is automatically recorded in the ledger.

### Learning Through Policy

When a mission succeeds or fails in a unique way, the system doesn't just "remember" it in a model's hidden context.
* **Policy Updates**: The CO can propose a change to a Playbook or a global ROE based on the outcome of a mission.
* **Durable Improvements**: These updates are written to the Garrison configuration, meaning the system actually gets smarter over time.

---

## 9. The Operational Ledger & Artifact Management

IronClaw does not rely on a model's "memory" to track progress. Instead, it uses a combination of a structured **Operational Ledger** and **Git-backed Artifact Management**.

### The Operational Ledger

The Ledger is an append-only record of every event that occurs within a Theater. It is the single source of truth for the system's state.

**Ledger Entry Types:**
* **Order Issued**: When the CO creates a new task.
* **Unit Claim**: When an Assault Unit or Fireteam begins work.
* **Signal**: Heartbeats or status updates sent by units during execution.
* **AAR (After-Action Report)**: The final summary of a completed task.
* **Integration Result**: Whether the work was accepted or rejected by Integration Command.

**Why the Ledger Matters:** If the system crashes or a unit is destroyed mid-task, the **Duty Officer** reads the Ledger to determine exactly where the mission stopped and how to resume it without repeating work.

### Artifact Management (Git-Backed)

Every mission operates within a Git repository. This provides "Physical State" to match the "Logical State" of the ledger.

**The Worktree System**

When an Order is issued, IronClaw creates a **Git Worktree**:
* This is a separate physical directory on the disk linked to the main repository.
* It allows multiple units to work on the same codebase simultaneously in total isolation.
* Units commit their progress locally within their worktree.

**The Promotion Pipeline**

Work never moves from a unit to the "main" branch automatically:
1. **Isolation**: Unit works in `worktrees/order_123`.
2. **Verification**: Integration Command checks the worktree.
3. **Promotion**: If valid, the changes are merged into the Theater's mainline.
4. **Cleanup**: The worktree is deleted, but the Git history remains.

### Federated References

IronClaw can track dependencies across different missions or even different Theaters using **Federated References**. A unit in "Theater A" can reference a specific file or AAR produced in "Theater B" using a unique hash.

### Auditability & The "Post-Mortem"

Because every ledger entry is timestamped and every file change is a Git commit, IronClaw provides 100% auditability.
* **Forensics**: If a bug is introduced, you can trace it back to the specific unit, the specific Order, and the specific model prompt that caused it.
* **Replayability**: You can "reset" a Theater to a previous state in the ledger and re-run a mission with a different model or policy.

### Summary of State

* **Logical State**: Stored in the Ledger (What was supposed to happen).
* **Physical State**: Stored in Git (What actually happened to the files).
* **Contextual State**: Stored in AARs (Why it happened).

---

## 10. Glossary & Operational Guarantees

This section provides a formal lexicon for the IronClaw environment and defines the hard guarantees the system provides to its operators.

### Key Terminology

**Command & Control (C2)**: The architectural framework used to manage, direct, and oversee autonomous units through structured hierarchy and feedback loops.

**Garrison**: The global management layer of IronClaw. It houses global configuration, the Duty Officer, and the master Playbook library.

**Theater**: A dedicated operational zone for a specific mission or project. Each Theater has its own repository, state, and Oversight units.

**Mission**: The high-level objective derived from user intent. A Mission is composed of multiple Operations.

**Operation**: A logical grouping of related tasks within a Mission.

**Order**: The smallest unit of work. A structured directive issued to an execution unit that includes objectives, constraints (ROE), and success criteria.

**Playbook**: A pre-validated, theater-level blueprint for generating Task Chains or Operations dynamically based on known patterns.

**Assault Unit**: An ephemeral execution unit responsible for completing exactly one Order before being destroyed.

**Fireteam**: A persistent capability unit designed for missions requiring domain continuity or iterative refinement over time.

**Integration Command**: The authority responsible for running quality gates, validating unit outputs, and promoting work to the mainline state.

**After-Action Report (AAR)**: The mandatory structured summary produced at the conclusion of every Order, documenting outcomes, changes, and discovered context.

### Oversight & Messaging

**Signal**: A structured, durable coordination message emitted by a unit to indicate a state transition or a specific exception.

**Escalation**: A controlled signal indicating that automation has reached a boundary it cannot cross and requires intervention.

**Integration Gate**: A validation checkpoint (tests, linting, policy checks) that must be satisfied before artifacts are promoted from a worktree.

**Federated Reference**: A structured identifier pointing to an artifact, result, or AAR produced outside the current Theater's immediate scope.

### Operational Guarantees

IronClaw is built to provide the following ironclad guarantees:

1. **Atomic Completion**: Every issued Order will either complete successfully or fail explicitly. There is no "unknown" state.
2. **State Durability**: No work is lost due to agent termination, crashes, or model timeouts. All progress is persisted to the filesystem and git history.
3. **Observable Failure**: Failures are never silent. They are recorded in the Ledger, flagged by Observers, and documented in AARs.
4. **Auditability**: Every change to the system state is traceable to a specific unit, a specific Order, and a specific point in time.
5. **Explainable Learning**: System improvements and policy updates are driven by historical mission outcomes, making "learning" reversible and transparent.
6. **Context Integrity**: Execution units only see the context they are granted. Information leakage between unrelated tasks is prevented by strict worktree isolation.

### The Final Doctrine

**"Units are disposable; the mission is permanent."**

IronClaw optimizes for the successful integration of work and the preservation of system state over the persistence of any individual AI process.
