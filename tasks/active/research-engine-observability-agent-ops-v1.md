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
- Remote checkpoint: 774b2cb5d8a99b9edd5238c6ca83383a6be30add
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 774b2cb5d8a99b9edd5238c6ca83383a6be30add
- Local clean: true

## Current stage

codex_allowance_telemetry_and_forecasting

## Next safe action

Start a fresh ChatGPT task executor from https://github.com/adamtrott78/workspace-control and this capsule. Keep research-engine-daemon.service inactive/dead. First implement and CI-validate two GitHub-side improvements on research-engine main@774b2cb5d8a99b9edd5238c6ca83383a6be30add: (1) allowance forecast reset-window grouping that tolerates precision/jitter in relative reset observations without pretending whole-percent readings are exact, and (2) a non-materializing low/high VERIFY replay batch that complements the already-completed median radius-0 replay with only two additional STANDARD/Terra calls. Also add a deterministic zero-model-call extraction provenance audit for the 9 existing papers if it can be implemented without delaying the calibration. Only after canonical CI should the Lambda fast-forward while stopped and run the bounded two-call calibration with one pre/post allowance reading pair. Do not START sustained research.

## Remaining work

- While the daemon remains stopped, fix allowance reset-window identity so relative-reset observations within the same real reset window tolerate UI precision/jitter; preserve raw observations and do not invent exact plan usage.
- Extend the non-materializing VERIFY calibration harness to select/replay the lowest-cost and highest-cost historical VERIFY jobs. The already-completed median replay is sample 1, so only two additional Terra calls are needed for a low/median/high radius-0 sample.
- Take one fresh 5-hour/weekly allowance reading immediately before the two-call replay batch and one immediately after. Store/display the integer UI movement as quantized/censored plan evidence rather than exact per-call percentage cost.
- For each low/median/high replay compare historical vs replay input/cached/output/reasoning tokens, context pages/chars, verified_equal, and accepted_evidence_ids_equal. If all three agree, retain radius 0 for the next bounded production calibration. If a job disagrees, rerun only that job at radius 1 before changing the global policy.
- Before spending more semantic allowance on EXTRACT optimization, perform a deterministic zero-model-call audit of the 9 existing papers: PDF page counts, evidence-bearing page counts, evidence density, evidence-page clustering, and extraction context size. Use that audit to choose whether page/section-selective EXTRACT is technically justified.
- After representative VERIFY validation and the EXTRACT provenance audit, choose the next bounded optimization experiment; do not resume sustained corpus expansion yet.
- After monitoring/tuning is validated, continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Radius-0 VERIFY context has only one live replay sample. Semantic agreement is exact on the median historical job, but low/high historical VERIFY jobs must be replayed before treating the result as representative.
- The ChatGPT/Codex usage UI reports whole percentages. The observed 86->85 five-hour and 96->95 weekly transitions are quantized bucket changes, not proof that one Terra call consumed exactly 1 percentage point.
- Allowance forecast reset-window grouping currently treats small derived reset_at differences as different windows. Relative UI reset readings have finite precision, so this must be fixed before burn-rate/ETA confidence can advance beyond CALIBRATING.
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
