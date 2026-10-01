<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/automated-research-engine-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: automated-research-engine-v1
- Title: Automated research engine v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Current stage

agentic_orchestration_v1

## Recovery restore point

- Identity: cfd5e354239cd1438bbb1da95d5435892427a67e
- stage=agentic_orchestration_v1
- last_validated_boundary=research-engine/main@cfd5e354239cd1438bbb1da95d5435892427a67e; non-agentic research vertical slice VALIDATED
- in_flight=research-engine PR #7 head agentic-orchestrator-v1@a5a5286a08a4120ca69b118443a3010b7333642f
- purpose=validate PostgreSQL autonomous cycle with transactional leases, crash recovery, retry, executor-tier routing, fan-out/fan-in, reconcilable planning, and durable HUMAN review gate
- resume=inspect PR #7 GitHub Actions for head a5a5286a08a4120ca69b118443a3010b7333642f; repair remotely if red, merge if green; then implement production headless executor adapter

## Next safe action

Inspect research-engine PR #7 / agentic-orchestrator-v1@a5a5286a08a4120ca69b118443a3010b7333642f. Repair any PostgreSQL orchestration failures remotely; merge when green. Then implement a production headless executor adapter while keeping orchestration provider-neutral.

## Remaining work

- Implement PostgreSQL-backed research runs and durable job queues with transactional worker leasing, heartbeat/lease expiry recovery, bounded retry, priorities, dependency/barrier semantics, and idempotent downstream planning.
- Implement executor-tier routing for DETERMINISTIC, CHEAP, STANDARD, STRONG, and HUMAN work without hard-coding a single model/provider into orchestration state.
- Implement the autonomous research-cycle stage graph: discovery -> screening -> acquisition fan-out -> extraction -> verification -> knowledge checkpoint -> synthesis -> gap generation -> novelty search fan-out -> novelty arbitration -> human review gate.
- Prove one complete autonomous dry-run cycle through the real PostgreSQL runtime, including worker crash/lease recovery, retry, fan-out/fan-in, heterogeneous executor routing, and a durable WAITING_HUMAN terminal state.
- Add a production executor adapter suitable for headless Lambda/Codex workers after the provider-neutral orchestration core passes.
- Then use the autonomous cycle to resume the deferred RF corpus expansion instead of manually shepherding individual papers.

## Blockers / gates

- None.