<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/automated-research-engine-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: automated-research-engine-v1
- Title: Automated research engine v1
- Status: BLOCKED_RUNTIME
- Capsule schema: v2

## Goal

Design and prove a provenance-preserving automated research engine that turns scholarly literature into structured evidence, durable knowledge, challenged research gaps, fundable research programs, and workspace-control-executable research projects.

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: 2ee1f6584178df68d1f01a219fb526d4745707bf

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: automated-research-engine-v1
- Remote checkpoint: 33339103d1a21842ff7479bd72782ab4dc42f9b9
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 219ef546381a471e5daac91ba524d9b685b8c26b
- Remote verified: true

## Next safe action

Audit acceptance-codex-rf-v1 persisted scientific state before resolving the pending human review: recompute the knowledge-checkpoint manifest/fingerprint from current authoritative records; inspect checkpoint-scoped works/artifacts/evidence/locators/verification, synthesis, two bounded gap candidates, novelty challenge provenance/counterevidence/reasoning, model usage ledger, and exact human-review payload. Do not approve the gate until those checks pass.

## Remaining work

- Perform the final scientific/provenance audit of the WAITING_HUMAN acceptance run.
- If the audit passes, resolve the human review as APPROVED and validate model_backed_acceptance_v1.
- Fix global budget-exhaustion semantics and implement/validate Codex plan-limit-aware pacing/backoff for continuous included-allowance operation.
- Then launch the first sustained RF literature expansion under hardened 24/7 controls.

## Blockers / gates

- model-backed acceptance has reached WAITING_HUMAN; final scientific-state/provenance audit and explicit human decision remain before acceptance can be marked complete.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
