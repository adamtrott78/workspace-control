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
- Remote checkpoint: bd62520387daa03d9c1b0cc4ab2365ccda85631c
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: e10fa79b939571fc2db8e1d6ac5afade2ceea7b2
- Local clean: true

## Current stage

codex_allowance_telemetry_and_forecasting

## Next safe action

Keep research-engine-daemon.service inactive/dead. On the Lambda, verify the research-engine checkout is clean on main@e10fa79b939571fc2db8e1d6ac5afade2ceea7b2, fetch and fast-forward only to canonical main@bd62520387daa03d9c1b0cc4ab2365ccda85631c, refresh the existing editable venv dependencies so fontTools is installed, then collect one pre-call usage reading through allowance-observe-paste, replay only source VERIFY job job:7b6ca4026f026bedaec4859e with RESEARCH_ENGINE_VERIFY_PAGE_RADIUS=1, collect one post-call usage reading through allowance-observe-paste, and finish with the daemon inactive/dead. Do not START sustained research.

## Remaining work

- Keep research-engine-daemon.service inactive/dead. Fast-forward the clean Lambda research-engine main checkout from e10fa79b939571fc2db8e1d6ac5afade2ceea7b2 to canonical bd62520387daa03d9c1b0cc4ab2365ccda85631c and refresh editable dependencies so fontTools is installed.
- Collect one fresh single-paste 5-hour/weekly allowance reading, rerun only source VERIFY job job:7b6ca4026f026bedaec4859e at RESEARCH_ENGINE_VERIFY_PAGE_RADIUS=1, then collect one fresh single-paste post reading. Keep the replay non-materializing and the daemon stopped.
- Compare the highest-cost radius-1 replay with its historical source: input/cached/output/reasoning tokens, context pages/chars, verified_equal, and accepted_evidence_ids_equal. If both agreement gates pass, use that result with the passing low/median radius-0 samples to decide the smallest safe global VERIFY radius. If radius 1 also disagrees, stop and inspect the source-specific verification context before any further allowance spend.
- Do not implement a global page-selective EXTRACT policy from the current audit; evidence spans 43/65 pages. Further EXTRACT work, if pursued, should begin with additional deterministic section-structure analysis rather than a semantic replay.
- Do not resume sustained corpus expansion yet.
- After tuning is validated, continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Radius-0 VERIFY is not globally validated: the lowest and median samples preserve accepted evidence IDs, but the highest-cost sample job:7b6ca4026f026bedaec4859e does not. Per the calibration gate, only that source may be rerun at radius 1 before changing global policy.
- The Lambda is still at research-engine main@e10fa79b939571fc2db8e1d6ac5afade2ceea7b2 and needs a stopped-daemon fast-forward to canonical bd62520387daa03d9c1b0cc4ab2365ccda85631c plus dependency refresh before the radius-1 retry.
- EXTRACT evidence spans 66.15% of PDF pages across the current 9-paper corpus; a global page-selective EXTRACT policy is not justified by the current deterministic audit.
- Sustained START remains gated on the targeted highest-cost radius-1 VERIFY result and the resulting global VERIFY policy decision.

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
