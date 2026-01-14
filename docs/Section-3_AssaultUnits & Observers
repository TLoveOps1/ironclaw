# 3. Detailed Unit Constraints — Assault Units & Observers

This section defines hard operational constraints for Theater-level units. These constraints are non-negotiable and exist to preserve system stability, auditability, and mission convergence. IronClaw does not rely on goodwill or “best practices”; it relies on enforced behavior.

---

## 3.1 Assault Unit (Primary Executor)

* **Role**: Atomic execution unit.
* **Lifecycle**: Ephemeral (spawn → execute → report → destroy).
* **Operational Doctrine**: “If there is an Order in your Orders Queue, you execute it” (ROE-EXEC).

### Core Constraints

1.  **Single-Order Focus**
    * An Assault Unit may execute only one Order at a time.
    * It must not poll for additional Orders.
    * It must not observe or supervise other units.
    * This guarantees determinism and prevents emergent coordination bugs.

2.  **Directory Containment**
    * Each Assault Unit is confined to its assigned operational worktree: `theaters/<theater>/worktrees/order_<order_id>/`.
    * No filesystem access is permitted outside this boundary.
    * No shared mutable state with other units is allowed.
    * All artifacts must be written inside this tree.
    * Violations are treated as execution failure.

3.  **Execution Propulsion**
    * Assault Units must always advance the Order state forward.
    * They must write intermediate state to disk.
    * They must emit ledger events for each meaningful step.
    * Units must never wait “idly” for external confirmation.
    * If blocked, the unit must record the blockage, emit a failure or escalation signal, and terminate. Stalling is considered a fault condition.

4.  **Self-Termination & Handoff**
    * Assault Units are responsible for initiating their own shutdown when context fills, logical work boundaries are reached, or the Order is complete/irrecoverable.
    * They must finalize artifacts, write an After-Action Report (AAR), and exit cleanly.
    * There is no concept of “lingering” or “idle” execution.

5.  **Git Discipline**
    * Units work only on their isolated worktree and commit all outputs locally.
    * They never merge or push to Theater mainline.
    * They never resolve conflicts beyond their scope.
    * All promotion authority belongs to Integration Command.

### Allowed Capabilities
* **May**: Call io.intelligence models using approved profiles, run allowed local tools, read referenced artifacts, and write structured outputs/reports.
* **May Not**: Modify policies, spawn other units, alter Orders, or bypass Integration Command.

---

## 3.2 Observer (Theater Oversight Unit)

* **Role**: Oversight and recovery.
* **Lifecycle**: Persistent (per-Theater).
* **Operational Doctrine**: “Detect, verify, escalate. Never execute.”

### Core Constraints

1.  **Oversight Only**
    * Observers are strictly prohibited from implementing changes, writing artifacts, or generating mission outputs.
    * Their authority is diagnostic and supervisory only.

2.  **Lifecycle Ownership**
    * Observers own the execution lifecycle within a Theater.
    * They track unit start/completion and verify clean operational state.
    * They determine when a unit is safe to decommission and ensure no work is lost during teardown.
    * No unit may be destroyed without Observer verification.

3.  **Stall Detection**
    * Observers continuously monitor for lack of ledger progress, no filesystem changes, exceeded budgets, or repeated retries without progress.
    * On detection, they may trigger a retry, escalate to the Duty Officer, or request reassignment of the Order.

4.  **Communication Discipline**
    * Observers must communicate sparingly and intentionally.
    * They notify higher command only for recovery-required conditions, repeated failures, policy violations, or integrity risks.
    * Routine success is not reported upward.

5.  **Integration Coordination**
    * Observers act as the bridge to Integration Command.
    * They validate that outputs are complete and artifacts are committed.
    * They signal readiness for integration and block promotion if integrity checks fail.

---

## 3.3 Prohibited Behaviors (All Units)

The following behaviors are explicitly forbidden and handled by the Watchdog Chain as failure events:
* Passive waiting without emitting state.
* Silent failure.
* Modifying Orders in-place.
* Cross-unit coordination outside Orders.
* Retaining uncommitted work at shutdown.
* Implicit authority escalation.

---

## 3.4 Why These Constraints Exist

These constraints ensure execution remains auditable, failures are recoverable, concurrency is manageable, and scaling does not create chaos. Learning is based on outcomes rather than hidden reasoning. IronClaw optimizes for mission completion, not agent comfort.