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

On the user's Lambda, stop research-engine-daemon.service if it is still restarting, require a clean main checkout at ec8baf481679aa86ee45b8b1b7dd47ed44846d6b, fetch and fast-forward exactly to 219ef546381a471e5daac91ba524d9b685b8c26b, confirm acceptance-codex-rf-v1 and its final bounded budget remain persisted, start the user daemon, and verify it remains active without idempotency restart-loop errors. Then observe the same run to WAITING_HUMAN or another durable gate.

## Remaining work

- Deploy research-engine main@219ef546381a471e5daac91ba524d9b685b8c26b to the Lambda and verify stable daemon startup with the same persisted acceptance run.
- Observe the remaining two bounded novelty searches and two novelty arbitrations to WAITING_HUMAN.
- At WAITING_HUMAN, verify evidence, Codex usage ledger, knowledge checkpoint, bounded novelty challenges, and human-review payload and validate model_backed_acceptance_v1.
- Implement/validate plan-limit-aware pacing/backoff for continuous operation under included weekly Codex allowance, then resume RF corpus expansion.

## Blockers / gates

- The migration-safe reconciliation fix is validated on canonical main but must be deployed to the Lambda before the final bounded acceptance run can continue.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
