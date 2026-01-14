
# 10. Glossary & Operational Guarantees

This section provides a formal lexicon for the IronClaw environment and defines the hard guarantees the system provides to its operators.

---

## 10.1 Key Terminology

### Command & Control (C2)
The architectural framework used to manage, direct, and oversee autonomous units through structured hierarchy and feedback loops.

### Garrison
The global management layer of IronClaw. It houses global configuration, the Duty Officer, and the master Playbook library.

### Theater
A dedicated operational zone for a specific mission or project. Each Theater has its own repository, state, and Oversight units.

### Mission
The high-level objective derived from user intent. A Mission is composed of multiple Operations.

### Operation
A logical grouping of related tasks within a Mission (e.g., "Database Migration").

### Order
The smallest unit of work. A structured directive issued to an execution unit that includes objectives, constraints (ROE), and success criteria.

### Playbook
A pre-validated, theater-level blueprint for generating Task Chains or Operations dynamically based on known patterns.

### Assault Unit
An ephemeral execution unit responsible for completing exactly one Order before being destroyed.

### Fireteam
A persistent capability unit designed for missions requiring domain continuity or iterative refinement over time.

### Integration Command
The authority responsible for running quality gates, validating unit outputs, and promoting work to the mainline state.

### After-Action Report (AAR)
The mandatory structured summary produced at the conclusion of every Order, documenting outcomes, changes, and discovered context.

---

## 10.2 Oversight & Messaging

### Signal
A structured, durable coordination message emitted by a unit to indicate a state transition or a specific exception.

### Escalation
A controlled signal indicating that automation has reached a boundary it cannot cross (e.g., security block, budget limit) and requires intervention.

### Integration Gate
A validation checkpoint (tests, linting, policy checks) that must be satisfied before artifacts are promoted from a worktree.

### Federated Reference
A structured identifier pointing to an artifact, result, or AAR produced outside the current Theater’s immediate scope.

---

## 10.3 Operational Guarantees

IronClaw is built to provide the following ironclad guarantees:

1.  **Atomic Completion**: Every issued Order will either complete successfully or fail explicitly. There is no "unknown" state.
2.  **State Durability**: No work is lost due to agent termination, crashes, or model timeouts. All progress is persisted to the filesystem and git history.
3.  **Observable Failure**: Failures are never silent. They are recorded in the Ledger, flagged by Observers, and documented in AARs.
4.  **Auditability**: Every change to the system state is traceable to a specific unit, a specific Order, and a specific point in time.
5.  **Explainable Learning**: System improvements and policy updates are driven by historical mission outcomes, making "learning" reversible and transparent.
6.  **Context Integrity**: Execution units only see the context they are granted. Information leakage between unrelated tasks is prevented by strict worktree isolation.

---

## 10.4 The Final Doctrine
**"Units are disposable; the mission is permanent."**
IronClaw optimizes for the successful integration of work and the preservation of system state over the persistence of any individual AI process.

```