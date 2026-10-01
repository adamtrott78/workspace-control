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

- Identity: 9698089965e7ed015e468e7e5f27453a791e760e
- stage=agentic_orchestration_v1
- last_validated_boundary=research-engine/main@9698089965e7ed015e468e7e5f27453a791e760e; PR #10 authoritative semantic pipeline PASS
- in_flight=research-engine PR #11 head agentic-v1-controller-search@751723e9849ceee3d639bc929483e1b914a11e6c
- slice=live Responses web_search provenance restricted to DISCOVERY/NOVELTY_SEARCH + restart-safe autonomous-run controller driving mixed workers to terminal/human gate
- resume=inspect PR #11 CI for head 751723e9849ceee3d639bc929483e1b914a11e6c; repair remotely if failing; merge if green; then classify agentic research v1 implementation complete pending first real model-authenticated autonomous run

## Next safe action

Inspect research-engine PR #11 for agentic-v1-controller-search@751723e9849ceee3d639bc929483e1b914a11e6c. Repair any CI failures remotely. If CI passes, merge PR #11, checkpoint agentic research v1 implementation complete, and proceed to the first real model-authenticated autonomous research run when a suitable runtime/API credential surface is available.

## Remaining work

- Enable live scholarly/web discovery for DISCOVERY and NOVELTY_SEARCH only; persist search query/source provenance in semantic execution metadata.
- Add a production-shaped autonomous controller command that starts a run, drives heterogeneous workers, recovers expired leases, and stops at WAITING_HUMAN/FAILED/COMPLETED.
- Validate the controller against real PostgreSQL with scripted semantic delegates and production deterministic materialization.
- Run one real model-backed autonomous research cycle on a model-authenticated runtime and inspect the human-review payload.
- Then harden 24/7 Lambda deployment: daemon supervision, concurrency/budgets/backpressure, and overnight reporting.

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
