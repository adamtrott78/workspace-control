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

Resume acceptance-codex-rf-v1 in place with a bounded budget increase: raise max_jobs_by_tier.STANDARD from 4 to 5 only to clear the consumed cap, and raise max_input_tokens from 220000 to 360000 for the remaining checkpoint/synthesis/gap/novelty stages. Keep max_output_tokens=40000, max_semantic_jobs=12, CHEAP=5, STRONG=3. Then observe persisted state only; do not manually orchestrate stages.

## Remaining work

- Perform one bounded in-place budget resume for acceptance-codex-rf-v1; preserve all other guardrails.
- Observe the same run until WAITING_HUMAN, another PAUSED_BUDGET, FAILED, or other gated/terminal state.
- If WAITING_HUMAN, verify source-grounded evidence, Codex usage ledger, knowledge checkpoint, novelty challenge state, and human-review payload and validate model_backed_acceptance_v1.
- After acceptance passes, resume RF corpus expansion through the daemon and operate continuously while pacing or pausing to stay within the included Codex allowance.

## Blockers / gates

- acceptance-codex-rf-v1 is safely PAUSED_BUDGET after exhausting only the STANDARD-tier job cap; bounded budget review/resume is required to continue the same run.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
