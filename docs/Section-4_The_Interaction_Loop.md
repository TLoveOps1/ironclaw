# 4. The Interaction Loop: Intent to Integration

IronClaw follows a rigid, linear progression for every user interaction. This ensures that no request is "lost" in conversation and that every output is the result of a structured mission.

---

## 4.1 Phase 1: Intent & Planning (Commanding Officer)
The loop begins when a user provides input via the chat interface.
1.  **Intent Extraction**: The CO analyzes the input to determine the objective.
2.  **METE Planning**: The CO performs **Mission Element Task Extraction**. It breaks the high-level intent into specific Operations and individual Orders.
3.  **The Theater Blueprint**: The CO selects or generates a **Playbook** (a reusable sequence of steps) or a **Task Chain** (a dynamic sequence for novel tasks).

---

## 2. Phase 2: Dispatch (The Ledger)
Once the plan is set, the CO does not "do" the work. It "orders" it.
1.  **Order Issuance**: The CO writes structured Orders into the **Orders Ledger**.
2.  **Unit Spawning**: The system instantiates the necessary **Assault Units** or **Fireteams**.
3.  **Queue Assignment**: Orders are pinned to the **Orders Queue**. The presence of an Order in this queue is a directive for the unit to begin execution immediately.

---

## 4.3 Phase 3: Execution (Theater Units)
This is where the actual labor occurs in isolation.
1.  **Worktree Initialization**: The unit is given a fresh git worktree.
2.  **Tool Use**: The unit utilizes io.intelligence and local tools to perform the task (coding, research, file editing).
3.  **Progress Signals**: As the unit works, it emits **Signals** to the ledger so the Observer and DO can track health.
4.  **Completion**: The unit writes its final changes to its local worktree and generates an **After-Action Report (AAR)**.

---

## 4.4 Phase 4: Oversight & Recovery (The Watchdog)
While execution is happening, the Watchdog Chain is active.
1.  **Patrol**: The **Observer** or **Duty Officer** scans the ledger.
2.  **Health Check**: If a unit is stalled or failing, the Watchdog intervenes (retries, reassigns, or escalates).
3.  **Integrity Check**: Once a unit claims completion, the Watchdog verifies the artifacts exist on disk before allowing the unit to terminate.

---

## 4.5 Phase 5: Integration & Promotion (Integration Command)
Work done in a worktree is not yet part of the "official" project state.
1.  **Validation**: **Integration Command** runs tests, linters, or policy checks against the unit's worktree.
2.  **Conflict Resolution**: If multiple units were working on related files, Integration Command merges the changes.
3.  **Promotion**: Validated work is committed to the Theater mainline state.

---

## 4.6 Phase 6: Synthesis & Learning (CO & Policy)
The loop closes back at the command level.
1.  **Outcome Review**: The CO reviews the AARs and the integrated state.
2.  **Response**: The CO provides a final update to the user via the chat interface.
3.  **Policy Update**: If the mission revealed a better way to handle a task, the **Policy** is updated so the system "learns" for future missions.



---

## Summary of the Loop
**User Input** → **Plan** → **Order** → **Execute** → **Verify** → **Integrate** → **Report**