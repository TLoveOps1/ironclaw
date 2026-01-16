# Filesystem Agent — Demo Playbook (Call Summary Mission)

This playbook defines a **single demo mission type** that uses the “filesystem + bash” pattern inside an IronClaw worktree.

**Goal:**  
Given a call transcript and some lightweight context files, an agent:

1. explores the worktree with **filesystem semantics** (`ls`, `cat`, `grep`)
2. pulls only the relevant context into the prompt
3. produces a structured summary + action items as files
4. leaves a durable AAR + ledger trail

IronClaw’s role is to enforce **isolation, durability, and auditability** around this pattern.

---

## 1. Mission type

**Name:** `filesystem_agent.call_summary`

**Mission request shape (high level):**

```json
{
  "mission_type": "filesystem_agent.call_summary",
  "call_id": "call_2026-01-15_0930",
  "inputs": {
    "transcript_markdown": "<full transcript as markdown>",
    "account_name": "Acme Corp",
    "contact_name": "Jane Smith"
  },
  "policy": {
    "max_tool_calls": 16,
    "max_tokens": 4000
  }
}
```

The CO turns this into an Order and passes it to Vault + Worker as usual.

## 2. Worktree layout for this mission

Inside the Vault-provisioned worktree for this order:

```text
theaters/demo/worktrees/<order_id>/
├── inputs/
│   ├── call.md                 # full transcript
│   └── mission.json            # raw mission request payload
├── context/
│   ├── account.json            # fake “CRM” context
│   └── playbook.md             # guidance for how to summarize
├── outputs/
│   ├── summary.md              # final human-readable summary
│   ├── action_items.md         # bullets with owners / due dates
│   └── model_output.txt        # raw final LLM response (for debugging)
└── aar.json                    # After Action Report (IronClaw contract)
```

### Example files

`inputs/call.md` (shortened example):

```markdown
# Call: Acme Corp — Renewal Discussion

Participant: Jane Smith (Acme), Tyler (Vendor)
Date: 2026-01-15

---

Jane: We're concerned about the recent uptime issues...
...
```

`context/account.json`:

```json
{
  "account_name": "Acme Corp",
  "industry": "SaaS",
  "current_plan": "Enterprise",
  "renewal_date": "2026-03-01",
  "account_health": "At risk"
}
```

`context/playbook.md`:

```markdown
# Summary Playbook

When summarizing a call:

1. Start with 2–3 sentence high-level summary.
2. Explicitly list:
   - risks
   - blockers
   - commitments
3. Extract action items with:
   - owner
   - due date (if mentioned)
   - short description
```

## 3. CO playbook for this mission

From IronClaw’s Command & Oversight perspective, this is a simple single-unit playbook.

### CO steps (conceptual)

1.  **Receive mission** `filesystem_agent.call_summary`.
2.  **Create run + order** in the Ledger:
    *   `run_id`
    *   `order_id`
    *   `mission_type`
3.  **Ask Vault to**:
    *   create a worktree for `<order_id>`
    *   initialize directory structure: `inputs/`, `context/`, `outputs/`
4.  **CO writes input artifacts** into the worktree:
    *   `inputs/call.md`
    *   `inputs/mission.json`
    *   `context/account.json`
    *   `context/playbook.md`
5.  **CO dispatches a Worker** with:
    *   `mission_type = filesystem_agent.call_summary`
    *   path to worktree
    *   tool policy (max tool calls, etc.)
6.  **When Worker completes**:
    *   CO records completion in the Ledger (paths to `outputs/*` and `aar.json`)
    *   CO returns a synthesized response to the user (e.g., embed `outputs/summary.md`)

## 4. Worker behavior (filesystem agent loop)

The Worker stays stateless and just runs a single tool-using agent episode inside the worktree.

### Tools exposed to the model (conceptual)

The Worker exposes a single tool to the model:

*   **bash tool** limited to the worktree root
*   Allowed commands: `ls`, `cat`, `grep`, `find`, maybe `head`, `tail`
*   No network access
*   No writing via bash; writes happen only by the Worker when the model returns a final answer

**Tool call schema** (what the model sees):

```json
{
  "tool": "bash",
  "command": "ls -R ."
}
```

**Worker executes this inside the worktree and returns**:

```json
{
  "tool": "bash",
  "command": "ls -R .",
  "stdout": "...",
  "stderr": ""
}
```

### Agent loop inside Worker (pseudocode)

Roughly:

1.  **Bootstrap system prompt** (inside Worker):
    *   You are an agent that can explore a filesystem using a bash tool (ls, cat, grep).
    *   The call transcript and context live under `inputs/` and `context/`.
    *   Your job is to produce a call summary and action items.
    *   Use the bash tool to inspect the files before answering.
2.  **Start a loop** (bounded by `max_tool_calls`):
    *   Call `io.intelligence` / LLM with:
        *   system prompt
        *   conversation history (including previous tool results)
    *   **If the model responds with a tool call**:
        *   Validate that command matches allowed pattern
        *   Execute it in the worktree
        *   Append the tool result to the conversation
    *   **If the model responds with a final answer instead of a tool call**:
        *   Break loop.
3.  **When final answer is produced**:
    *   Parse or post-process into:
        *   `outputs/summary.md`
        *   `outputs/action_items.md`
    *   Write `outputs/model_output.txt` (raw content).
    *   Create `aar.json` with:
        *   mission metadata
        *   list of tool calls (commands + timestamps + status)
        *   paths of written artifacts
    *   `git add` the outputs + aar.json, then `git commit` with a message like:
        `filesystem_agent.call_summary: summarized call <call_id>`
    *   Exit with success or failure code.

## 5. Example AAR structure

`aar.json` (high level):

```json
{
  "order_id": "order_20260115_093000",
  "mission_type": "filesystem_agent.call_summary",
  "status": "completed",
  "started_at": "2026-01-15T15:31:05Z",
  "finished_at": "2026-01-15T15:31:42Z",
  "tool_calls": [
    {
      "index": 0,
      "tool": "bash",
      "command": "ls -R .",
      "exit_code": 0
    },
    {
      "index": 1,
      "tool": "bash",
      "command": "cat inputs/call.md",
      "exit_code": 0
    },
    {
      "index": 2,
      "tool": "bash",
      "command": "cat context/account.json",
      "exit_code": 0
    }
  ],
  "artifacts": {
    "summary": "outputs/summary.md",
    "action_items": "outputs/action_items.md",
    "raw_model_output": "outputs/model_output.txt"
  }
}
```

This AAR is what lets IronClaw:

*   audit behavior
*   debug tool use
*   replay missions if needed

## 6. CLI / Operator view (demo path)

Assuming your CLI is:

```bash
python3 garrison/cli/ironclaw.py
```

You can imagine a UX like:

```bash
# 1) Bring the stack up
python3 garrison/cli/ironclaw.py stack up

# 2) Run a filesystem-agent mission using local transcript file
python3 garrison/cli/ironclaw.py mission call-summary \
  --transcript path/to/transcript.md \
  --account-name "Acme Corp" \
  --contact-name "Jane Smith"
```

The CLI would:

1.  wrap this into a mission payload
2.  send to CO
3.  CO runs the playbook above
4.  then prints the final summary (read from `outputs/summary.md`).

## 7. Done criteria for this playbook

You can call this demo “done” when:

*   **Running the CLI command**:
    *   creates a new run + order
    *   provisions a worktree
    *   writes `inputs/` and `context/` as described
*   **Worker**:
    *   calls the LLM at least once with a bash tool
    *   uses at least one tool call (`ls` / `cat`) before answering
    *   writes `outputs/summary.md`, `outputs/action_items.md`, and `aar.json`
    *   commits them to the worktree repo
*   **Ledger**:
    *   records order status transitions `queued` → `running` → `completed`
    *   stores references to:
        *   worktree path
        *   commit SHA
        *   key artifacts (`summary.md`, `aar.json`)
*   **Operator can**:
    *   inspect the worktree on disk
    *   open `aar.json` and see exactly which files/commands the agent used

At that point, you have a full, end-to-end filesystem agent demo running on top of IronClaw, aligned with the Vercel filesystem + bash pattern but wrapped in your durability + audit guarantees.
