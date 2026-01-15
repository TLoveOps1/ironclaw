# IronClaw

IronClaw is a microservices-based mission execution and orchestration framework.

## Quick Start
To get the system running in its v1 configuration:
1. Navigate to the CLI directory: `cd garrison/cli`
2. Start the stack: `./ironclaw.py stack up`
3. Send a mission: `./ironclaw.py chat "Hello IronClaw"`

## Documentation
- [IronClaw v1 Specification](docs/IronClaw_v1.md): The authoritative definition of system guarantees, architectural invariants, and non-goals.
- [Phase G (Stack UX) Guide](garrison/cli/README_STACK.md): Managing and monitoring the full microservices stack.
- [Service Documentation](garrison/): Individual READMEs for Ledger, Vault, Worker, CO, and Observer services.

## Architecture
The system follows a strict separation of concerns across five core microservices:
1. **Ledger**: Append-only event store and authoritative mission state.
2. **Vault**: Git worktree management and mission archival.
3. **Worker**: Stateless unit execution and artifact generation.
4. **CO (Command & Oversight)**: Centralized mission orchestration.
5. **Observer**: Theater-level monitoring and anomaly signaling.

---
*IronClaw v1 is formally frozen and verified.*
