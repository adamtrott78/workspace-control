<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-observability-agent-ops-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-observability-agent-ops-v1
- Title: Research Engine Observability, Agent Operations & Chat Bridge v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Build a low-overhead, provenance-preserving operations layer for the autonomous research engine that provides a live terminal HUD, durable per-agent telemetry and throughput metrics, empirical Codex 5-hour/weekly allowance forecasting, ChatGPT-visible status mirroring, and a safe asynchronous bridge for agents to request high-level reasoning from ChatGPT without paid API fallback or direct scientific-state mutation.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 6ba5cbb8623eadbcd8ee6d2c68a3821dcd63e121
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e10fa79b939571fc2db8e1d6ac5afade2ceea7b2
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 774b2cb5d8a99b9edd5238c6ca83383a6be30add
- Local clean: true

## Current stage

codex_allowance_telemetry_and_forecasting

## Next safe action

Keep research-engine-daemon.service inactive/dead. On the Lambda, verify the research-engine checkout is clean on main at 774b2cb5d8a99b9edd5238c6ca83383a6be30add, fetch and fast-forward only to canonical research-engine main@e10fa79b939571fc2db8e1d6ac5afade2ceea7b2, then run bash deploy/run-verify-calibration.sh. The runner must perform the deterministic zero-model EXTRACT provenance audit, collect one fresh 5-hour/weekly usage reading pair immediately before the bounded batch, replay only the lowest-cost and highest-cost historical VERIFY jobs at radius 0 (two STANDARD/Terra calls total), collect one fresh post-batch reading pair, and finish with the daemon inactive/dead. Preserve the complete output for comparison with the already-completed median replay. Do not START sustained research.

## Remaining work

- On the Lambda, while research-engine-daemon.service remains inactive/dead, verify the checkout is clean on main and fast-forward research-engine from 774b2cb5d8a99b9edd5238c6ca83383a6be30add to canonical e10fa79b939571fc2db8e1d6ac5afade2ceea7b2.
- Run bash deploy/run-verify-calibration.sh. Preserve the deterministic EXTRACT provenance audit, one fresh 5-hour/weekly pre-batch usage reading pair, the lowest-cost and highest-cost radius-0 VERIFY replay outputs, one post-batch reading pair, the updated HUD, and the final inactive/dead daemon check.
- Compare low/median/high historical vs replay input/cached/output/reasoning tokens, context pages/chars, verified_equal, and accepted_evidence_ids_equal. If all three agree, retain radius 0 for the next bounded production calibration. If a sample disagrees, rerun only that failing source at radius 1 before changing the global policy.
- Use the zero-model EXTRACT audit across the 9 existing papers to decide whether page/section-selective EXTRACT is technically justified before spending any EXTRACT semantic allowance.
- After representative VERIFY validation and the EXTRACT provenance audit, choose the next bounded optimization experiment; do not resume sustained corpus expansion yet.
- After monitoring/tuning is validated, continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Radius-0 VERIFY context has only one live replay sample. The low/high replay machinery is canonical and CI-validated, but the two bounded Lambda STANDARD/Terra calls have not yet been executed.
- The ChatGPT/Codex usage UI reports whole percentages. The ledger/forecaster now preserves these as censored/quantized measurements, but the next empirical evidence still requires one fresh pre-batch and one fresh post-batch reading pair around the two calls.
- The deterministic EXTRACT provenance audit is implemented and CI-validated but still needs to run against the 9 preserved Lambda papers before an EXTRACT optimization is selected.
- Sustained START remains gated on representative VERIFY calibration and a bounded tuning decision.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
Invariant: every fresh-chat initialization or handoff prompt for this task must include the full workspace-control repository URL shown above.
