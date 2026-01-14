# 8. Extensibility & Playbooks

IronClaw is designed to be extended without modifying the core command-and-control logic. This is achieved through **Playbooks** and **Tool Definition**, which allow the system to adapt to new domains while maintaining strict operational discipline.

---

## 8.1 Playbooks: Predefined Mission Logic
A Playbook is a structured template for common missions. Instead of the Commanding Officer (CO) "guessing" how to handle a request, it retrieves the appropriate Playbook to ensure consistency.

* **Structure**: Playbooks define a sequence of Operations, required unit roles, and specific success criteria.
* **Version Control**: Playbooks are stored in the Garrison repository and are versioned like code.
* **Customization**: While the structure is fixed, the CO can inject mission-specific variables (e.g., target URLs, file paths) into the Playbook at runtime.

### Example Playbook Categories:
* **Feature-Branch**: Planning, coding, testing, and PR creation.
* **Infrastructure-Audit**: Security scanning, dependency checks, and reporting.
* **Research-Deep-Dive**: Web search, document synthesis, and bibliography generation.

---

## 8.2 Task Chains: Dynamic Execution
For novel requests that do not fit a Playbook, the CO generates a **Task Chain**.
* **Linear & Branching**: Tasks can be strictly sequential or branch out into parallel work.
* **State Propagation**: Outputs from one task in the chain are automatically passed as inputs (Federated References) to the next.
* **Evaluation**: The CO evaluates the progress of the chain after each major milestone to decide if the plan needs to be adjusted.

---

## 8.3 Rules of Engagement (ROE)
Extensibility is governed by ROE. You can create new ways for the system to work, but they must follow these rules:
* **ROE-EXEC**: Units must always advance the state; stalling is a failure.
* **ROE-ISOLATE**: All work must happen in a dedicated worktree.
* **ROE-REPORT**: No task is complete until an After-Action Report is written.

---

## 8.4 Custom Tool Integration
New capabilities are added to IronClaw via **Tool Profiles**. 
1.  **Definition**: Define the tool’s input/output schema (compatible with io.intelligence).
2.  **Permissions**: Assign the tool to specific roles (e.g., only Assault Units can use `shell_exec`; only Integration Command can use `git_merge`).
3.  **Logging**: Every tool call is automatically recorded in the ledger, ensuring that "extensibility" never leads to "opacity."

---

## 8.5 Learning Through Policy
When a mission succeeds or fails in a unique way, the system doesn't just "remember" it in a model's hidden context.
* **Policy Updates**: The CO can propose a change to a Playbook or a global ROE based on the outcome of a mission.
* **Durable Improvements**: These updates are written to the Garrison configuration, meaning the system actually gets smarter and more efficient over time.