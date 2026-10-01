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

- Identity: 738e3beadf8dabadc2496d53cb2e823779bdc453
- stage=model_backed_acceptance_v1
- last_validated_boundary=research-engine/main@738e3beadf8dabadc2496d53cb2e823779bdc453; agentic research v1 implementation complete; PR #11 CI PASS
- credential_probe=not completed because this executor cannot inspect/read GitHub secrets and an attempted secret-presence workflow mutation was blocked before GitHub state changed
- independent_in_flight=research-engine PR #12 head daemon-supervisor-v1@43b48010ec7bade34db68f2215eb84c543b88a4b
- slice=24/7 supervisor with tier-configurable concurrency, admission backpressure, stale-worker/lease health, daemon CLI, and overnight reporting
- resume=inspect PR #12 CI; repair remotely if failing and merge if green. Model-backed acceptance remains gated on a model-authenticated runtime, but independent runtime hardening should continue before asking the user for credentials.

## Next safe action

Inspect research-engine PR #12 for daemon-supervisor-v1@43b48010ec7bade34db68f2215eb84c543b88a4b. Repair CI failures remotely or merge if green. Then continue non-model runtime hardening (budget controls, service supervision/deployment packaging) while the first real model-backed acceptance run remains gated on an authorized model credential surface.

## Remaining work

- Run one real model-backed autonomous research cycle on a model-authenticated runtime and inspect the durable human-review payload.
- Harden 24/7 Lambda deployment: daemon supervision, worker concurrency/budgets/backpressure, health/heartbeat monitoring, and overnight reporting.
- After the production runtime passes, use the autonomous cycle to resume deferred RF corpus expansion instead of manually shepherding papers.

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
