# IronClaw task_list_microservices.md (microservices decomposition)

Goal: take the MVP pipeline and split it into services with clear boundaries.

Legend:
- [ ] Not started
- [x] Done
- [~] In progress

---

## Phase A — Service boundaries (design)
- [ ] Define APIs and ownership:
  - [ ] control plane vs execution plane
  - [ ] what is in git vs what is in ledger
- [ ] Choose messaging/runtime:
  - [ ] Celery+Redis (simpler) OR Temporal (stronger workflows)
- [ ] Choose auth for internal services:
  - [ ] shared secret / mTLS / local-only
- [ ] Done criteria:
  - [ ] You have a 1-page “service contract” doc listing endpoints + events

---

## Phase B — API Gateway (chat surface)
Service: `api_gateway`
- [ ] Endpoints:
  - [ ] `POST /chat`
  - [ ] `GET /runs/{run_id}`
  - [ ] `GET /orders/{order_id}`
- [ ] Input validation + rate limiting
- [ ] Returns:
  - [ ] final response (sync) OR run_id (async)
- [ ] Done criteria:
  - [ ] Chat requests create Runs and return a stable identifier + response strategy

---

## Phase C — Commanding Officer service (orchestrator)
Service: `co_service`
- [ ] METE planning module (v0):
  - [ ] classify request
  - [ ] generate 1–N Orders
  - [ ] choose model profiles
- [ ] Dispatch logic:
  - [ ] enqueue tasks to queue/workflow engine
- [ ] Fan-in synthesis:
  - [ ] read artifacts + AAR
  - [ ] format response
- [ ] Done criteria:
  - [ ] CO can orchestrate multi-step runs without touching worker internals

---

## Phase D — Ledger service (events + snapshots)
Service: `ledger_service`
- [ ] Store:
  - [ ] runs
  - [ ] orders
  - [ ] events (append-only)
  - [ ] snapshots (derived)
- [ ] Endpoints:
  - [ ] `POST /events`
  - [ ] `GET /runs/{id}`
  - [ ] `GET /orders/{id}`
- [ ] Done criteria:
  - [ ] System can restart and reconstruct state from ledger

---

## Phase E — Theater/Vault service (git + worktrees)
Service: `vault_service`
- [ ] Create Theater repo (if missing)
- [ ] Create worktree for Order
- [ ] Write initial Order payload into worktree (`task.md`, `state.json`)
- [ ] Commit helper utilities
- [ ] Remove/archive worktrees safely
- [ ] Done criteria:
  - [ ] Workers can request “worktree ready” via API and get a path + metadata

---

## Phase F — Worker runtime (Assault Units)
Service: `worker_service`
- [ ] Worker accepts a job:
  - [ ] order_id + worktree path
  - [ ] model profile
  - [ ] tool policy
- [ ] Loads `.env` (or secret injection) and calls io.intelligence
- [ ] Writes artifacts + AAR
- [ ] Commits changes
- [ ] Emits completion/failure events to ledger_service
- [ ] Done criteria:
  - [ ] Workers are fully stateless; deleting the container loses nothing important

---

## Phase G — Observer service (Theater oversight)
Service: `observer_service`
- [ ] Patrol loop per Theater:
  - [ ] detect stalled orders
  - [ ] detect orphaned worktrees
  - [ ] verify completion criteria
- [ ] Escalation events:
  - [ ] `RECOVERY_REQUIRED`
  - [ ] `INTEGRATION_READY`
- [ ] Done criteria:
  - [ ] Stalls are detected and reissued automatically (within policy)

---

## Phase H — Integration Command service (validation + promotion)
Service: `integration_service`
- [ ] Validate artifacts and AAR schema
- [ ] Apply gates (tests/lint/policy)
- [ ] Promote from worktree → Theater mainline (merge/cherry-pick)
- [ ] Emit `INTEGRATED` or `INTEGRATION_FAILED` events
- [ ] Done criteria:
  - [ ] Promotions are deterministic and fully recorded

---

## Phase I — Duty Officer + Sentinel (system reliability)
Services: `do_service`, `sentinel_service`
- [ ] DO patrol:
  - [ ] scan ledger for overdue orders
  - [ ] reissue/rollback/disable on policy triggers
- [ ] Sentinel audit:
  - [ ] verify DO health and effectiveness
  - [ ] alert/trigger failover
- [ ] Done criteria:
  - [ ] Killing workers/services mid-run does not permanently break missions

---

## Phase J — Learning service (policy updates)
Service: `learning_service`
- [ ] Compute success metrics by:
  - [ ] model profile
  - [ ] task type
  - [ ] tool usage
- [ ] Update routing policy (explainable):
  - [ ] prefer profiles with better outcomes
  - [ ] adjust retries/timeouts
- [ ] Store user preferences (structured)
- [ ] Done criteria:
  - [ ] Routing decisions change based on logged outcomes and are inspectable

---

## Phase K — Deployment & ops
- [ ] Docker-compose (local) or k8s (prod)
- [ ] Secret management (move off `.env` in prod)
- [ ] Observability:
  - [ ] metrics (latency, success rate, queue depth)
  - [ ] logs (structured)
  - [ ] traces (optional)
- [ ] Backups:
  - [ ] ledger DB backups
  - [ ] Theater repo backups
- [ ] Done criteria:
  - [ ] You can deploy, restart, and recover without manual fixes
