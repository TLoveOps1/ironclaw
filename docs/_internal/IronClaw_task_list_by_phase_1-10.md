# IronClaw task list by phase (start → finish)
Use this as a checklist to build the full platform. Each phase ends with a concrete “done” condition.

### Phase 0 — Foundations and safety rails
- [ ] Create base directory layout (~/ironclaw/garrison, ~/ironclaw/theaters)
- [ ] Decide ledger storage: SQLite (local) or Postgres (server)
- [ ] Define global policies (budgets, max units, allowed tools)
- [ ] Create .env strategy (per-Garrison or per-Theater) + permissions (chmod 600)
- [ ] Create model profiles (planner/executor/verifier) for io.intelligence
- [ ] Define Order schema (JSON fields, status lifecycle)
- [ ] Define AAR schema (artifacts list, model info, summary, next actions)
- [ ] Add basic logging conventions (structured logs)
- **Done when:** you can point to the directory layout + schemas + policies and they’re stable

### Phase 1 — Theater bootstrap (git as durable state)
- [ ] Create a Theater repo (git init, initial commit)
- [ ] Create worktree root (theaters/<name>/worktrees)
- [ ] Implement “create worktree for order” command/process
- [ ] Implement “remove worktree safely” command/process
- **Done when:** you can create/remove worktrees repeatedly without git errors

### Phase 2 — Single-unit execution contract (the core primitive)
- [ ] Unit reads Order input (from file or args)
- [ ] Unit loads .env (python-dotenv) and calls io.intelligence
- [ ] Unit writes artifacts to outputs/
- [ ] Unit writes aar.json
- [ ] Unit commits artifacts + AAR in its worktree
- [ ] Unit exits cleanly
- **Done when:** Order → Unit → io.intelligence → Artifact → AAR → Commit works reliably

### Phase 3 — Orders + Runs (durable mission tracking)
- [ ] Create Run record (mission instance) on user input
- [ ] Append Orders to an Orders log (JSONL)
- [ ] Maintain per-unit Orders Queue file(s)
- [ ] Track Order status transitions (queued/running/completed/failed)
- **Done when:** you can list runs, list orders, and see accurate statuses after restarts

### Phase 4 — Commanding Officer (CO) minimal orchestration
- [ ] Implement /chat endpoint (FastAPI) or CLI equivalent
- [ ] METE: convert user message into 1–N Orders
- [ ] Select Theater (create if needed)
- [ ] Create worktree(s) for issued Orders
- [ ] Dispatch unit execution (subprocess / task queue)
- [ ] Collect artifacts + AARs
- [ ] Synthesize a single chat response from results
- **Done when:** one chat request can spawn a unit and return its artifact as the reply

### Phase 5 — Multi-unit execution (fan-out / fan-in)
- [ ] Define standard multi-unit Playbook: Research → Draft → Verify
- [ ] Spawn multiple units in parallel with separate worktrees
- [ ] Define dependency rules (Draft waits for Research, Verify waits for Draft)
- [ ] Merge results into a single response (fan-in)
- **Done when:** the CO can reliably run 2–3 units and combine outputs

### Phase 6 — Observer (Theater oversight)
- [ ] Implement stalled detection (no events / no file changes / timeout)
- [ ] Verify unit completion criteria (artifact exists, AAR valid, git clean)
- [ ] Quarantine orphan worktrees (unit died but worktree exists)
- [ ] Emit escalation signals when recovery is required
- **Done when:** stalled units are detected and flagged without human babysitting

### Phase 7 — Integration Command (validation and promotion)
- [ ] Define validation gates (schema checks, tests, lint, policy)
- [ ] Implement “promote” step: cherry-pick or merge from worktree into Theater mainline
- [ ] Handle conflicts deterministically (fail + escalate or resolve policy)
- [ ] Record integration decisions in ledger/events
- **Done when:** accepted outputs can be promoted to mainline with a recorded gate pass

### Phase 8 — Duty Officer patrol + Sentinel audit
- [ ] Implement DO patrol loop (periodic scan of Orders, queues, worktrees)
- [ ] Auto-reissue stuck Orders (with retry limits)
- [ ] Enforce budgets (max concurrency, timeouts)
- [ ] Implement Sentinel: verify DO is running and responsive
- **Done when:** you can kill a unit mid-run and DO recovers it automatically

### Phase 9 — Learning and adaptation (policy-based, auditable)
- [ ] Track outcomes (success/failure, latency, retries, user corrections)
- [ ] Maintain skill scores per profile/model/task type
- [ ] Update routing policy based on outcomes
- [ ] Extract stable user preferences into structured storage
- [ ] Add artifact index for retrieval (lightweight summaries)
- **Done when:** the system measurably changes routing/behavior based on logged outcomes

### Phase 10 — Operations hardening (production readiness)
- [ ] Containerize workers (optional) or isolate execution sandbox
- [ ] Add secrets handling (dotenv for local; secret manager for prod)
- [ ] Add observability (metrics for queue depth, success rate, latency)
- [ ] Add rate limits + backoff for io.intelligence calls
- [ ] Add backup/restore plan for ledger and repos
- **Done when:** you can run long sessions without manual cleanup or silent failures

### Phase 11 — UX layer (general chat product)
- [ ] Chat UI (web/mobile) calling /chat
- [ ] Progress view for Runs (optional but useful)
- [ ] “Explain” mode: show AAR summaries when user asks
- [ ] “Artifacts” view: browse outputs per run/order
- **Done when:** users can chat normally and the system orchestrates invisibly