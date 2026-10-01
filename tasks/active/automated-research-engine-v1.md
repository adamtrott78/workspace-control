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

Submit one conservative autonomous RF research topic through the already-running Lambda daemon using a fixed run ID and explicit durable semantic-job/token budgets. Monitor persisted run state. If PAUSED_BUDGET, inspect budget usage and resume only with a bounded increase; if WAITING_HUMAN, verify evidence, usage ledger, checkpoint, novelty state, and human-review payload.

## Remaining work

- Submit one real Codex-backed autonomous RF research cycle with a conservative per-run budget and let the persistent daemon orchestrate it.
- Verify durable WAITING_HUMAN with source-grounded evidence, Codex usage ledger, knowledge checkpoint, novelty challenge state, and human-review payload; bounded budget resume is allowed if necessary.
- After acceptance passes, resume RF corpus expansion through the daemon and operate continuously while pacing or pausing to stay within the included Codex allowance.
- Tune worker concurrency/model-tier budgets and allowance-aware pacing from observed first-run consumption, latency, and quality.

## Blockers / gates

- The only remaining model-backed acceptance boundary is one real conservative autonomous RF research cycle through the persistent Codex-backed daemon to durable WAITING_HUMAN.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
