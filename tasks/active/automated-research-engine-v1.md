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
- resume=probe an authorized runtime for OPENAI_API_KEY/model authentication without exposing credentials; if available run research-engine autonomous-run on a bounded real topic to WAITING_HUMAN and inspect the payload; if unavailable record the genuine credential boundary and continue non-model 24/7 daemon hardening

## Next safe action

Probe an authorized execution surface for model authentication without exposing secrets. Prefer a GitHub Actions presence/runtime probe if available. If OPENAI_API_KEY/model authentication is available, run a bounded real autonomous research cycle from research-engine/main@738e3beadf8dabadc2496d53cb2e823779bdc453 to WAITING_HUMAN and inspect the persisted review payload. If credentials are unavailable, record the credential boundary and continue independent 24/7 daemon hardening.

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
