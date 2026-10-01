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

Observe acceptance-codex-rf-v1 persisted state only. The daemon is stable on migration-safe reconciliation. Expected remaining bounded progress is completion of the two allowed novelty searches, completion of two novelty arbitrations, then deterministic transition to WAITING_HUMAN. If WAITING_HUMAN, perform the final evidence/usage/checkpoint/novelty/human-review audit.

## Remaining work

- Observe the stable final bounded acceptance run to WAITING_HUMAN or another durable gate.
- At WAITING_HUMAN, verify source-grounded evidence, Codex usage ledger, knowledge checkpoint, bounded novelty challenges, and human-review payload and validate model_backed_acceptance_v1.
- Implement/validate plan-limit-aware pacing/backoff for continuous operation under the included weekly Codex allowance.
- Then resume RF corpus expansion and tune concurrency/model tiers against observed allowance consumption and research quality.

## Blockers / gates

- acceptance-codex-rf-v1 is RUNNING stably on the final bounded novelty graph; model-backed acceptance awaits WAITING_HUMAN or another durable gate.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
