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

Resume the same run with a minimal bookkeeping increase that clears the global exhausted predicate and leaves headroom after two remaining STRONG arbitrations: CHEAP=8 (no additional CHEAP work expected), STRONG=5, max_semantic_jobs=16, STANDARD=5, with a bounded input-token ceiling sufficient for two final STRONG calls. Then observe to WAITING_HUMAN.

## Remaining work

- Perform the final arbitration-only budget resume for the two queued STRONG NOVELTY_ARBITRATE jobs.
- Observe acceptance-codex-rf-v1 to WAITING_HUMAN and perform the final evidence/usage/checkpoint/novelty/human-review audit.
- Fix the global budget-exhaustion semantics so a saturated unused tier does not pause unrelated queued tiers, and validate plan-limit-aware pacing/backoff for continuous included-allowance operation.
- Then resume RF corpus expansion and tune concurrency/model tiers against observed allowance consumption and research quality.

## Blockers / gates

- acceptance-codex-rf-v1 is safely PAUSED_BUDGET with only two STRONG NOVELTY_ARBITRATE jobs remaining; pause reason is exact CHEAP cap exhaustion despite no remaining CHEAP work.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
