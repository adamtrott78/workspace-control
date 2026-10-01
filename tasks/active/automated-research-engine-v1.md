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
- Remote checkpoint: 64295c4f0d102fb02552f25881f01970d39cb304
- Remote verified: true

## Next safe action

Genuine runtime/human-auth boundary. On the user's Lambda, update the existing research-engine checkout to exact main@64295c4f0d102fb02552f25881f01970d39cb304, verify or install a current Codex CLI, and authenticate Codex with the user's ChatGPT account. Do not configure OPENAI_API_KEY and do not use paid API fallback. Return only non-secret version/auth/status output. Then initialize persistent PostgreSQL plus the native user daemon and run one conservative-budget autonomous research topic to WAITING_HUMAN.

## Remaining work

- Update the Lambda research-engine checkout to exact main@64295c4f0d102fb02552f25881f01970d39cb304; verify/install a current Codex CLI and authenticate it with the user's ChatGPT account. Do not configure OPENAI_API_KEY.
- Run PostgreSQL persistently and the research daemon natively as the signed-in user so Codex can reuse host ChatGPT authentication without copying credentials into a container.
- Run one real Codex-backed autonomous research cycle with a conservative per-run budget and verify it reaches durable WAITING_HUMAN with source-grounded evidence, Codex usage ledger, knowledge checkpoint, novelty challenge state, and human-review payload.
- After acceptance passes, use the daemon—not manual chat orchestration—to resume RF corpus expansion and operate continuously while pacing work to stay within the included Codex allowance.
- Tune worker concurrency/model-tier budgets from observed Codex allowance consumption, latency, and quality after the first real run.

## Blockers / gates

- The remaining acceptance test requires the user's Lambda runtime with Codex CLI authenticated to the user's ChatGPT plan. Current connected tooling cannot operate that host or complete the interactive ChatGPT login flow.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
