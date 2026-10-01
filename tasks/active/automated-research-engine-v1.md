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

On the user's Lambda, install the checked-in research-engine user systemd unit, enable/start it as the signed-in ChatGPT/Codex user, verify service/worker health and user lingering state, and do not submit a research topic yet. Do not configure OPENAI_API_KEY or use the openai-api-development Compose profile. Return only non-secret status/log/report output.

## Remaining work

- Install/enable the user systemd research daemon as the signed-in ChatGPT/Codex user and verify restart/health behavior.
- Run a tiny direct Codex-plan structured-output smoke test using the configured production model route before submitting autonomous work.
- Run one real Codex-backed autonomous research cycle with a conservative per-run budget and verify it reaches durable WAITING_HUMAN with source-grounded evidence, Codex usage ledger, knowledge checkpoint, novelty challenge state, and human-review payload.
- After acceptance passes, resume RF corpus expansion through the daemon and operate continuously while pacing or pausing to stay within the included Codex allowance.
- Tune worker concurrency/model-tier budgets and allowance-aware pacing from observed Codex consumption, latency, and quality after the first real run.

## Blockers / gates

- The remaining acceptance test requires enabling the validated user systemd daemon and exercising one real Codex-backed autonomous research cycle on the user's Lambda.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
