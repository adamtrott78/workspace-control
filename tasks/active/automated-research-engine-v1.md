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

On the user's Lambda while acceptance-codex-rf-v1 remains PAUSED_BUDGET, verify the only untracked path is src/research_engine/__pycache__/, delete only that generated directory, require a clean checkout, fetch and fast-forward main from 03babb404e9e6a254deec38fea6ea5ab3b8b05ad to exact ec8baf481679aa86ee45b8b1b7dd47ed44846d6b, restart the user daemon, and return post-deploy run/job/budget state. Do not resume the budget yet; first reconcile/cancel the surplus novelty queue under the bounded planner.

## Remaining work

- Deploy research-engine main@ec8baf481679aa86ee45b8b1b7dd47ed44846d6b to the safely paused Lambda and restart the native user daemon.
- Reconcile acceptance-codex-rf-v1 under the bounded planner so surplus queued novelty jobs are cancelled/ignored deterministically; then inspect the remaining bounded graph.
- Apply only the bounded budget changes needed for the remaining novelty arbitration/human-review path and reach WAITING_HUMAN.
- Verify source-grounded evidence, Codex usage ledger, knowledge checkpoint, bounded novelty challenges, and human-review payload; validate model_backed_acceptance_v1.
- Implement/validate plan-limit-aware pacing/backoff for 24/7 operation under included weekly Codex allowance, then resume RF corpus expansion.

## Blockers / gates

- The validated bounded-fanout/cache-hygiene build has not yet been deployed to the Lambda. The acceptance run is safely PAUSED_BUDGET, so deployment may proceed after removing only the verified generated __pycache__ directory.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
