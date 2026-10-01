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

## Goal

Design and prove a provenance-preserving automated research engine that turns scholarly literature into structured evidence, durable knowledge, challenged research gaps, fundable research programs, and workspace-control-executable research projects.

## Current stage

agentic_orchestration_v1

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: 2ee1f6584178df68d1f01a219fb526d4745707bf

## Recovery restore point

- Identity: cfd5e354239cd1438bbb1da95d5435892427a67e
- stage=agentic_orchestration_v1
- last_validated_boundary=research-engine/main@cfd5e354239cd1438bbb1da95d5435892427a67e; full non-agentic research vertical slice VALIDATED and GitHub Actions 36807507382 PASS
- manual_corpus_expansion=deferred intentionally; temporary acquisition branches are not the active path
- resume=branch from cfd5e354239cd1438bbb1da95d5435892427a67e and implement provider-neutral durable orchestration: research runs, job queue, worker leases/retry/recovery, executor tiers, stage fan-out/fan-in, human gate; prove autonomous PostgreSQL cycle before production model adapter

## Next safe action

Build agentic orchestration in adamtrott78/research-engine from main@cfd5e354239cd1438bbb1da95d5435892427a67e. First implement the provider-neutral PostgreSQL job/run state machine, transactional leases/retry/recovery, executor-tier routing, stage fan-out/fan-in, and explicit human-review gate. Validate one fully autonomous scripted cycle in GitHub Actions/PostgreSQL before adding a production Codex/model executor adapter.

## Remaining work

- Implement PostgreSQL-backed research runs and durable job queues with transactional worker leasing, heartbeat/lease expiry recovery, bounded retry, priorities, dependency/barrier semantics, and idempotent downstream planning.
- Implement executor-tier routing for DETERMINISTIC, CHEAP, STANDARD, STRONG, and HUMAN work without hard-coding a single model/provider into orchestration state.
- Implement the autonomous research-cycle stage graph: discovery -> screening -> acquisition fan-out -> extraction -> verification -> knowledge checkpoint -> synthesis -> gap generation -> novelty search fan-out -> novelty arbitration -> human review gate.
- Prove one complete autonomous dry-run cycle through the real PostgreSQL runtime, including worker crash/lease recovery, retry, fan-out/fan-in, heterogeneous executor routing, and a durable WAITING_HUMAN terminal state.
- Add a production executor adapter suitable for headless Lambda/Codex workers after the provider-neutral orchestration core passes.
- Then use the autonomous cycle to resume the deferred RF corpus expansion instead of manually shepherding individual papers.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
