# 7. Configuration & State

IronClaw separates configuration, operational state, and historical record. Each has a distinct storage model and lifecycle to ensure reliability, auditability, and controlled evolution over time. Nothing critical is inferred implicitly; everything meaningful is either configured, recorded, or derived.

---

## 7.1 Configuration Layers (Override Hierarchy)
Configuration is resolved through a strict precedence order. Higher layers override lower ones.

1.  **System Defaults (Lowest Priority)**: Hardcoded safe fallbacks with minimal assumptions. Used only if no other configuration is present.
2.  **Garrison Configuration**: Global policies, limits, model profiles, io.intelligence routing, and default Playbooks.
    * *Location:* `garrison/config/`
3.  **Theater Configuration**: Mission- or project-specific overrides, tool allowlists, budget adjustments, and integration rules.
    * *Location:* `theaters/<theater>/config/`
4.  **Run-Level Overrides (Highest Priority)**: Temporary constraints for a specific mission, such as tightened budgets. These are explicitly scoped and non-persistent.

**Rule:** Configuration is never modified by execution units.

---

## 7.2 Model & Tool Profiles (io.intelligence)
IronClaw treats models as interchangeable execution resources selected by policy rather than hardcoding. Profiles define:
* Model identifier (io.intelligence-compatible).
* Temperature and sampling parameters.
* Cost and latency expectations.
* Allowed task types and safety/output constraints.

Routing policies determine which profile is used for each Order type, enabling model swapping without refactors and cost-aware execution.

---

## 7.3 Operational State
Operational state represents what is happening "now." It is stored as structured records in the ledger, minimal filesystem markers, and derived views.
* **Examples:** Active Orders, unit status, retry counts, and escalation flags.
* **Characteristics:** Mutable, queryable, and derived from events where possible.

---

## 7.4 Events as Data (Immutable History)
All significant actions emit events. Events are the ground truth of the system.
* **Properties:** Append-only, timestamped, linked (to Run, Order, and unit), and never modified or deleted.
* **Records:** Task assignment, execution start/stop, failures, retries, integration decisions, and escalations.

---

## 7.5 Derived State (Snapshots)
To avoid replaying the entire event log for every query, IronClaw maintains versioned snapshots (e.g., summarized Order state, Run progress).
* Snapshots are treated as cache, not truth.
* If a snapshot is lost, it is regenerated from the event log.

---

## 7.6 Labels as State
Fast-changing conditions are tracked using lightweight labels (e.g., `mode.degraded`, `order.blocked.external`). These support fast queries and are always backed by events to ensure auditability is not sacrificed for performance.

---

## 7.7 State Recovery
IronClaw assumes state corruption and interruption are possible. Recovery guarantees ensure:
* Events are replayable and snapshots are regenerable.
* Worktrees preserve partial outputs.
* Orders can be reissued safely.
* No single store is a single point of failure.

---

## 7.8 Why This Separation Matters
This model ensures:
* Configuration changes are deliberate.
* Execution cannot mutate policy.
* History is never lost.
* Live state is inspectable.
* Learning and adaptation are explainable.

IronClaw treats state as infrastructure, not as side effects.

---

## 7.9 io.intelligence Integration Model
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