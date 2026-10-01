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
- Remote checkpoint: 03babb404e9e6a254deec38fea6ea5ab3b8b05ad
- Remote verified: true

## Next safe action

Observe persisted state for acceptance-codex-rf-v1 without manually orchestrating jobs. If WAITING_HUMAN, verify source-grounded evidence, Codex usage ledger, knowledge checkpoint, novelty challenge state, and human-review payload. If PAUSED_BUDGET again, inspect exact exhausted reason and apply only a bounded increase if justified.

## Remaining work

- Observe acceptance-codex-rf-v1 until WAITING_HUMAN, another PAUSED_BUDGET, FAILED, or other gated/terminal state.
- If WAITING_HUMAN, verify source-grounded evidence, Codex usage ledger, knowledge checkpoint, novelty challenge state, and human-review payload and validate model_backed_acceptance_v1.
- If PAUSED_BUDGET again, inspect durable usage and raise only the specific exhausted guardrail needed to complete acceptance.
- After acceptance passes, resume RF corpus expansion through the daemon and operate continuously while pacing or pausing to stay within the included Codex allowance.

## Blockers / gates

- acceptance-codex-rf-v1 is RUNNING again after bounded budget review; final model-backed acceptance awaits its next durable gated or terminal state.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
