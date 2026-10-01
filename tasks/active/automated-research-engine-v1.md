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

Observe rf-open-world-corpus-expansion-v1 under the hardened daemon. Allow automatic Codex plan-limit backoff/resume and tier-aware budget routing to operate without intervention. Inspect only if the run reaches WAITING_HUMAN, PAUSED_BUDGET, FAILED, or a provider backoff persists unexpectedly beyond its recorded blocked_until. Do not auto-approve future scientific human-review decisions.

## Remaining work

- Observe rf-open-world-corpus-expansion-v1 through discovery, screening, acquisition, extraction, verification, checkpoint, synthesis, bounded gap generation, novelty challenge, and its next human-review gate.
- At the next human-review gate, audit the new corpus checkpoint/evidence and decide explicitly whether to approve or continue expansion.
- Use observed throughput and Codex allowance consumption to tune sustained batch size and tier budgets without enabling paid API fallback.

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
