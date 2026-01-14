# 6. Unit Lifecycle & Decommissioning

IronClaw treats execution units as consumable instruments, not long-lived actors. Units exist solely to execute Orders and must leave the system in a known, verifiable state when finished. There is no idle pool; a unit is either executing or gone.

---

## 6.1 Unit Lifecycle States
All execution units progress through a strict lifecycle. Transitions are explicit and recorded.

* **Spawned**: The unit process/container is created. Identity and scope are assigned, and an Orders Queue is attached.
* **Active**: The unit has claimed an Order. An operational worktree is created, and execution begins immediately under ROE-EXEC.
* **Blocked**: The unit encounters an external dependency or constraint. The blockage is recorded with reason and context. The unit must then either resolve it or fail fast.
* **Completed**: Order objectives are met. Artifacts are written and committed, and an After-Action Report (AAR) is produced.
* **Failed**: The Order cannot be completed within constraints. Failure is explicit and documented. No partial state is discarded.
* **Decommissioned**: The unit exits cleanly. No further execution occurs, and cleanup is authorized.

---

## 6.2 Clean Shutdown Requirements
Before decommissioning, a unit must satisfy all of the following conditions:
1.  All artifacts are written to disk.
2.  The Git worktree is in a consistent state.
3.  The After-Action Report (AAR) is complete.
4.  Ledger events are flushed.
5.  No untracked or dangling state remains.

**Note:** Failure to meet these conditions triggers recovery processes rather than destruction.

---

## 6.3 Decommissioning Authority
Units may not self-destruct arbitrarily. Authority rules are as follows:
* **Assault Units**: May request decommissioning after completion or failure. The Observer must verify the state before approval.
* **Fireteams**: Decommissioned only by explicit command. Persistent state must be preserved.
* **Observers**: Authorize unit teardown after verification.
* **Duty Officer**: May forcibly terminate units during recovery but must preserve all reachable state.

---

## 6.4 Forced Termination (Recovery Mode)
Forced termination occurs only when a unit is unresponsive or violating constraints.
1.  **Snapshot**: The system snapshots the current filesystem state.
2.  **Record**: The termination reason is recorded in the ledger.
3.  **Terminate**: The process or container is terminated.
4.  **Reissue**: The Order is reissued to a fresh unit.

The original unit is considered failed, but its work is not lost.

---

## 6.5 Orphan Detection
IronClaw actively scans for orphaned execution state, including:
* Worktrees with no active unit.
* Units with no ledger heartbeat.
* Orders marked active with no progress.

Orphans are quarantined, inspected, and either resumed by a new unit or archived as failed attempts. No state is deleted without inspection.

---

## 6.6 Why This Lifecycle Exists
This lifecycle guarantees:
* Predictable system behavior and recoverable failures.
* Bounded resource usage and clean scaling across many units.
* Detailed post-mortem analysis for every single failure.

IronClaw optimizes for mission completion and auditability, not long-lived execution comfort.