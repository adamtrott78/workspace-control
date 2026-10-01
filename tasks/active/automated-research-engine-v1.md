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
- Remote checkpoint: ec8baf481679aa86ee45b8b1b7dd47ed44846d6b
- Remote verified: true

## Next safe action

Resume acceptance-codex-rf-v1 in place with only the final bounded allowance needed for two remaining CHEAP novelty searches and two STRONG novelty arbitrations: max_semantic_jobs=15, CHEAP=7, STANDARD=5, STRONG=4, with a bounded input-token ceiling increase sufficient for four remaining model calls. Then observe persisted state only until WAITING_HUMAN or another budget/failure gate.

## Remaining work

- Perform the final bounded in-place budget resume for the two remaining CHEAP novelty searches and two STRONG novelty arbitrations.
- Observe acceptance-codex-rf-v1 to WAITING_HUMAN and verify evidence, Codex usage ledger, knowledge checkpoint, bounded novelty challenges, and human-review payload.
- Validate model_backed_acceptance_v1 after WAITING_HUMAN evidence passes.
- Implement/validate plan-limit-aware pacing/backoff for continuous operation under the included weekly Codex allowance, then resume RF corpus expansion.

## Blockers / gates

- acceptance-codex-rf-v1 is safely PAUSED_BUDGET with only the bounded final graph remaining: two CHEAP novelty searches and two STRONG novelty arbitrations.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
