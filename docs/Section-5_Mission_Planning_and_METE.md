# 5. Mission Planning & METE (Mission Element Task Extraction)

Mission planning is the process of converting ambiguous user intent into a high-precision execution roadmap. IronClaw uses a framework called **METE** to ensure that planning is structured, repeatable, and decoupled from the execution phase.

---

## 5.1 The METE Framework
METE stands for **Mission Element Task Extraction**. It is the formal logic used by the Commanding Officer (CO) to translate a request into actionable work.

1.  **Mission (The Goal)**: The overarching objective defined by the user (e.g., "Build a data ingestion pipeline for the CRM").
2.  **Elements (The Components)**: The logical blocks required to complete the mission (e.g., API Connector, Database Schema, Logging Layer).
3.  **Tasks (The Actions)**: The atomic steps within each element (e.g., "Write the OAuth2 handshake script").
4.  **Extraction (The Output)**: The process of packaging these tasks into structured **Orders**.

---

## 5.2 The Planning Process

When a mission begins, the CO follows these steps:

### 1. Situation Assessment
The CO scans the current environment, existing files, and relevant policy documents to understand the context of the request.

### 2. Strategy Selection
The CO decides how to approach the problem:
* **Playbook Path**: If the mission matches a known pattern (e.g., a standard deployment), the CO uses a predefined Playbook.
* **Task Chain Path**: If the mission is novel, the CO generates a dynamic chain of dependent tasks.

### 3. Dependency Mapping
The CO identifies which tasks must happen sequentially and which can happen in parallel. This information is encoded into the Orders so that the Watchdog Chain knows when to release a unit.

### 4. Operational Budgeting
The CO assigns a "budget" to the mission, including:
* **Time limits** (TTL) for each order.
* **Retry limits** for failures.
* **Tool access** level for the units.

---

## 5.3 Output: The Order Packet
The result of METE is a set of **Order Packets**. Every packet contains:
* **Objective**: A concise description of the desired outcome.
* **Reference Material**: Links to existing code, documentation, or previous AARs.
* **Rules of Engagement (ROE)**: Specific constraints the unit must follow (e.g., "Do not use external libraries," "Follow PEP8").
* **Success Criteria**: How the unit (and the Integration Command) will know the task is finished.

---

## 5.4 Dynamic Re-Planning
Planning does not end when execution starts. IronClaw supports **asynchronous refinement**:
* If an Assault Unit discovers a blocker (e.g., a missing API key), it records this in its AAR.
* The CO receives the report, adjusts the mission plan, and issues new Orders to resolve the blocker.
* This creates a "self-correcting" planning loop that can handle surprises without human intervention.

---

## 5.5 Why METE?
By forcing the CO to extract tasks into a formal structure, IronClaw avoids the "black box" problem of typical AI agents. You can see exactly what the system planned to do *before* it starts doing it, allowing for auditability and manual course correction if the strategy is flawed.