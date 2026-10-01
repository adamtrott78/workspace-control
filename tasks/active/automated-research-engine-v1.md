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
- Remote checkpoint: 6a423e0fd38283687cae2eb060405a2a82643450
- Remote verified: true

## Next safe action

Run the single fail-closed Lambda launch script prepared from canonical research-engine main@6a423e0fd38283687cae2eb060405a2a82643450. It must stop the daemon, require a clean fast-forward to that exact commit, initialize the additive schema, normalize conservative production env/backoff settings without any OPENAI_API_KEY, clean only the known unreferenced legacy acceptance gap materializations while preserving raw semantic results, recompute acceptance invariants/checkpoint fingerprint, approve the pending acceptance human review, submit the first sustained bounded RF corpus expansion, restart the daemon, and verify stable unattended operation.

## Remaining work

- Execute the single fail-closed Lambda deployment/cleanup/approval/launch script against research-engine main@6a423e0fd38283687cae2eb060405a2a82643450.
- Record the resulting sustained-run ID, daemon health, provider-backoff state if any, and acceptance approval as the post-launch restore point.
- Observe the sustained RF corpus expansion through Codex allowance backoffs and its next human-review gate; do not silently auto-approve scientific decisions.

## Blockers / gates

- Launch-ready code is validated on canonical main; Lambda still needs exact deployment, schema migration, provenance-preserving acceptance cleanup/audit, explicit acceptance approval, and sustained-run submission.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
