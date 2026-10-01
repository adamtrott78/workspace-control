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
- Remote checkpoint: aafde498d728e6e04a65902095f269d3ef9a7901
- Remote verified: true

## Next safe action

On the user's Lambda, read acceptance-codex-rf-v1 durable run/budget/job state first. If the run is still RUNNING, do not change the checkout or restart the daemon; return the status so the bounded existing budget can gate it. If it is PAUSED_BUDGET or WAITING_HUMAN, fast-forward the clean research-engine checkout from 03babb404e9e6a254deec38fea6ea5ab3b8b05ad to exact main@aafde498d728e6e04a65902095f269d3ef9a7901, restart the user systemd daemon to load the bounded-fanout planner, and return post-restart non-secret run/job/health state. Do not configure OPENAI_API_KEY.

## Remaining work

- Inspect the current durable state of acceptance-codex-rf-v1 and deploy research-engine main@aafde498d728e6e04a65902095f269d3ef9a7901 only at a safe paused/human gate boundary.
- Use the bounded-fanout planner to salvage/cancel surplus queued novelty work in the same acceptance run, then apply only the budget changes justified by the remaining bounded graph.
- Reach WAITING_HUMAN and verify source-grounded evidence, Codex usage ledger, knowledge checkpoint, bounded novelty challenges, and human-review payload.
- After acceptance passes, implement/validate plan-limit-aware pacing/backoff so 24/7 operation pauses cleanly when the included weekly Codex allowance is unavailable rather than exhausting job retries.
- Then resume RF corpus expansion through the daemon and tune concurrency/model tiers against observed allowance consumption and quality.

## Blockers / gates

- The bounded novelty-fanout fix is validated but not yet deployed to the user's Lambda. The current acceptance run's latest status must be read before restarting the daemon so no active semantic job is raced.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
