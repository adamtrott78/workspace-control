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

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: 2ee1f6584178df68d1f01a219fb526d4745707bf

## Recovery restore point

- Identity: f5f007960cb2a67d880874135e904aa209559238
- stage=agentic_orchestration_v1
- last_validated_boundary=research-engine/main@f5f007960cb2a67d880874135e904aa209559238; PR #9 mixed deterministic/semantic worker cycle PASS
- external_runtime_prepared=research-engine/semantic-context-materialization@d0888c4c3ee84be78ae6f6b3bf6535b443b95c2e
- validation_target=hydrate EXTRACT/VERIFY from exact artifact text; hydrate SYNTHESIZE/GAP/NOVELTY from knowledge checkpoints; materialize extraction, verification, synthesis, gaps, and novelty challenges with crash-safe semantic result caching
- resume=inspect/create PR for d0888c4c3ee84be78ae6f6b3bf6535b443b95c2e; run GitHub Actions PostgreSQL CI; repair failures remotely; merge only after authoritative end-to-end agent materialization test passes

## Next safe action

Open a pull request from semantic-context-materialization@d0888c4c3ee84be78ae6f6b3bf6535b443b95c2e to research-engine/main. Use GitHub Actions PostgreSQL/pgvector CI to validate exact source/checkpoint hydration, crash-safe semantic result caching, and authoritative EXTRACT/VERIFY/SYNTHESIZE/GAP/NOVELTY materialization. Repair remotely and merge only when green.

## Remaining work

- Implement PostgreSQL-backed research runs and durable job queues with transactional worker leasing, heartbeat/lease expiry recovery, bounded retry, priorities, dependency/barrier semantics, and idempotent downstream planning.
- Implement executor-tier routing for DETERMINISTIC, CHEAP, STANDARD, STRONG, and HUMAN work without hard-coding a single model/provider into orchestration state.
- Implement the autonomous research-cycle stage graph: discovery -> screening -> acquisition fan-out -> extraction -> verification -> knowledge checkpoint -> synthesis -> gap generation -> novelty search fan-out -> novelty arbitration -> human review gate.
- Prove one complete autonomous dry-run cycle through the real PostgreSQL runtime, including worker crash/lease recovery, retry, fan-out/fan-in, heterogeneous executor routing, and a durable WAITING_HUMAN terminal state.
- Add a production executor adapter suitable for headless Lambda/Codex workers after the provider-neutral orchestration core passes.
- Then use the autonomous cycle to resume the deferred RF corpus expansion instead of manually shepherding individual papers.

## Blockers / gates

- None.