# 9. The Operational Ledger & Artifact Management

IronClaw does not rely on a model's "memory" to track progress. Instead, it uses a combination of a structured **Operational Ledger** and **Git-backed Artifact Management**. This ensures that every action taken by an AI unit is recorded, versioned, and recoverable.

---

## 9.1 The Operational Ledger
The Ledger is an append-only record of every event that occurs within a Theater. It is the single source of truth for the system's state.

### Ledger Entry Types:
* **Order Issued**: When the CO creates a new task.
* **Unit Claim**: When an Assault Unit or Fireteam begins work.
* **Signal**: Heartbeats or status updates sent by units during execution.
* **AAR (After-Action Report)**: The final summary of a completed task.
* **Integration Result**: Whether the work was accepted or rejected by Integration Command.

### Why the Ledger Matters:
If the system crashes or a unit is destroyed mid-task, the **Duty Officer** reads the Ledger to determine exactly where the mission stopped and how to resume it without repeating work.

---

## 9.2 Artifact Management (Git-Backed)
Every mission operates within a Git repository. This provides "Physical State" to match the "Logical State" of the ledger.

### The Worktree System
When an Order is issued, IronClaw creates a **Git Worktree**. 
* This is a separate physical directory on the disk linked to the main repository.
* It allows multiple units to work on the same codebase simultaneously in total isolation.
* Units commit their progress locally within their worktree.

### The Promotion Pipeline
Work never moves from a unit to the "main" branch automatically.
1.  **Isolation**: Unit works in `worktrees/order_123`.
2.  **Verification**: Integration Command checks the worktree.
3.  **Promotion**: If valid, the changes are merged into the Theater's mainline.
4.  **Cleanup**: The worktree is deleted, but the Git history remains.

---

## 9.3 Federated References
IronClaw can track dependencies across different missions or even different Theaters using **Federated References**.
* A unit in "Theater A" can reference a specific file or AAR produced in "Theater B" using a unique hash.
* This allows the system to build complex, cross-domain projects while keeping the actual work isolated.

---

## 9.4 Auditability & The "Post-Mortem"
Because every ledger entry is timestamped and every file change is a Git commit, IronClaw provides 100% auditability.
* **Forensics**: If a bug is introduced, you can trace it back to the specific unit, the specific Order, and the specific model prompt that caused it.
* **Replayability**: You can "reset" a Theater to a previous state in the ledger and re-run a mission with a different model or policy to see if the outcome improves.

---

## 9.5 Summary of State
* **Logical State**: Stored in the Ledger (What was supposed to happen).
* **Physical State**: Stored in Git (What actually happened to the files).
* **Contextual State**: Stored in AARs (Why it happened).