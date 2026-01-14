# 1. Overview & Vision

IronClaw is an **agentic command-and-control (C2) environment** built to power a general-purpose conversational system. It autonomously plans, executes, and completes complex missions using ephemeral AI units while persisting all meaningful state outside the model.

IronClaw is not an IDE tool or developer assistant; it is a **mission execution system** that presents itself through a chat interface.

---

### Core Functionality
Behind its single conversational interface, IronClaw performs several critical functions:
* **Decomposes** user intent into atomic, auditable tasks.
* **Dispatches** short-lived execution units.
* **Persists** all work in git-backed operational directories.
* **Validates** and integrates results.
* **Learns** over time through durable policy and outcome tracking.

> **Core Philosophy:** All AI units are disposable. All mission state is permanent.

---

### The Core Problem vs. IronClaw’s Solution
Modern agent systems often fail because they lose context, coordination is manual, and "learning" is trapped inside volatile model memory. IronClaw treats these failures as expected conditions rather than edge cases.

| Challenge | IronClaw Approach |
| :--- | :--- |
| **Agent context loss** | All work state is persisted in git-backed operational artifacts. |
| **Unreliable execution** | Orders are durable; failed units are replaced. |
| **Manual coordination** | C2 structure with explicit tasking. |
| **Scaling agents** | Ephemeral units + strict lifecycles. |
| **Hidden failure** | Event logs + After-Action Reports. |
| **Vanishing "Learning"** | Policy updates driven by outcomes, not memory. |

---

### Design Goals & Principles
IronClaw is built on the following non-negotiable principles:
* **Durability First:** No meaningful work lives only in model context.
* **Ephemeral Execution:** Units exist only to complete Orders, then are destroyed.
* **Explicit Control Flow:** Every action is traceable to an Order, Task Chain, or Playbook.
* **Asynchronous Integrity:** The system converges on success even when individual steps fail.
* **Chat as Interface:** Conversation is the input/output layer—not the control plane.

---

### Technology Foundation
Implemented primarily in **Python**, the system utilizes a distributed-system architecture:
* **io.intelligence:** The model execution backend (OpenAI-compatible API).
* **Git Repositories + Worktrees:** Used for durable operational state.
* **Structured Ledgers:** Records for events, Orders, and outcomes.
* **Queue-based Execution:** Enables scalable, asynchronous unit dispatch.

### Mental Model: The Operational Flow
IronClaw is a mission system that "speaks" chat. Its operational flow follows a strict progression:
**Intent** → **Orders** → **Execution Units** → **Persistent Artifacts** → **Validation** → **Response** → **Policy Update**.