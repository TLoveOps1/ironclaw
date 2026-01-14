# IronClaw task_list_mvp.md (MVP-first)

Legend:
- [ ] Not started
- [x] Done
- [~] In progress

Goal: reach a working loop: **Chat → Order → Worktree → Unit → io.intelligence → Artifact + AAR → Response**.

---

## Phase 0 — Foundations (minimum required)
- [ ] Create base layout:
  - [ ] `~/ironclaw/garrison/`
  - [ ] `~/ironclaw/theaters/`
- [ ] Decide MVP ledger: SQLite (local)
- [ ] Define policy defaults (keep small):
  - [ ] max units per request
  - [ ] max retries
  - [ ] max wall-clock seconds per unit
- [ ] Secrets:
  - [ ] `.env` location (recommend per-Theater at first)
  - [ ] enforce permissions (`chmod 600`)
- [ ] Define schemas (v0):
  - [ ] Order JSON fields + statuses
  - [ ] AAR JSON fields
- [ ] Define io.intelligence profiles (v0):
  - [ ] `planner_fast`
  - [ ] `executor_default`
- [ ] Done criteria:
  - [ ] You can point to a single doc or file that defines schemas + defaults

---

## Phase 1 — Theater bootstrap (git durability)
- [ ] Create Theater repo:
  - [ ] `git init`
  - [ ] initial commit
- [ ] Create worktree root:
  - [ ] `theaters/<theater>/worktrees/`
- [ ] Procedure: create worktree for Order
- [ ] Procedure: remove worktree safely
- [ ] Done criteria:
  - [ ] You can create/remove `order_001` worktree repeatedly without git errors

---

## Phase 2 — Unit contract (single execution unit)
- [ ] Python venv for Theater:
  - [ ] `.venv` created
  - [ ] `openai` installed
  - [ ] `python-dotenv` installed
- [ ] Unit script (runs inside worktree) does:
  - [ ] load `.env`
  - [ ] call io.intelligence (OpenAI-compatible base_url)
  - [ ] write `outputs/model_output.txt`
  - [ ] write `aar.json`
  - [ ] `git add/commit`
  - [ ] exit
- [ ] Done criteria:
  - [ ] Running unit produces committed artifact + AAR every time

---

## Phase 3 — Minimal Commanding Officer (no microservices yet)
Pick one for MVP (CLI first is simplest):
- [ ] CLI `co_run.py` OR FastAPI `/chat` (choose one)
- [ ] METE-lite:
  - [ ] turn a user message into exactly 1 Order
- [ ] CO responsibilities:
  - [ ] choose Theater (or create)
  - [ ] create worktree for Order
  - [ ] write `task.md` / Order file into worktree
  - [ ] run unit (subprocess)
  - [ ] read artifact + AAR
  - [ ] return response to user
- [ ] Done criteria:
  - [ ] One command (or one `/chat` call) returns a model-generated response via the unit pipeline

---

## Phase 4 — Durable tracking (Runs + Orders log)
- [ ] Create `run_id` per mission
- [ ] Append Orders to `orders.jsonl`
- [ ] Track status transitions:
  - [ ] queued → running → completed/failed
- [ ] Store links:
  - [ ] worktree path
  - [ ] commit SHA(s)
- [ ] Done criteria:
  - [ ] After restart, you can list runs/orders and see correct status + artifacts

---

## Phase 5 — Multi-unit Playbook (optional but high value)
- [ ] Implement Playbook: Research → Draft → Verify
- [ ] Dispatch 2–3 units with dependencies
- [ ] Fan-in merge into one response
- [ ] Done criteria:
  - [ ] CO returns a single final answer that cites/uses upstream artifacts

---

## Phase 6 — Observer-lite (basic patrol)
- [ ] Detect stall:
  - [ ] no new commits after N seconds
  - [ ] unit process exited non-zero
- [ ] Verify completion:
  - [ ] artifact exists
  - [ ] AAR exists + valid JSON
- [ ] Reissue Order once (single retry policy)
- [ ] Done criteria:
  - [ ] You can kill the unit mid-run and the system reissues and completes

---

## Phase 7 — Cleanup & sustainability
- [ ] Safe decommission:
  - [ ] archive worktree OR remove worktree after integration decision
- [ ] Prune old worktrees by policy
- [ ] Done criteria:
  - [ ] Worktrees don’t accumulate forever; nothing important is deleted prematurely
