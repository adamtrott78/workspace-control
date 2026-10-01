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
- Local HEAD: 051a3b0c9828de411812b0a519a070a2aa87683b
- Local clean: true

## Current stage

codex_allowance_telemetry_and_forecasting

## Next safe action

On the Lambda, keep research-engine-daemon.service inactive/dead, clean fast-forward research-engine main from 051a3b0c9828de411812b0a519a070a2aa87683b to exact validated 774b2cb5d8a99b9edd5238c6ca83383a6be30add, then execute `bash deploy/run-verify-calibration.sh`. At its pre/post prompts enter the current ChatGPT UI percent LEFT and relative reset values. The runner applies only the additive calibration schema, performs exactly one non-materializing STANDARD/Terra VERIFY replay against the median historical VERIFY job, persists operational calibration telemetry, renders the updated HUD, and must finish with the daemon inactive/dead. Do not START sustained research yet.

## Remaining work

- Fast-forward the stopped Lambda to research-engine main@774b2cb5d8a99b9edd5238c6ca83383a6be30add.
- Run deploy/run-verify-calibration.sh. Record fresh pre/post percent-left/reset readings from the ChatGPT usage UI around the single Terra replay.
- Review historical versus replay VERIFY input/cached/uncached tokens, page count, verified_equal, accepted_evidence_ids_equal, and the new HUD CALIBRATION panel.
- If agreement is preserved, keep page radius 0 and quantify projected sustained-run savings. If agreement differs, set RESEARCH_ENGINE_VERIFY_PAGE_RADIUS=1 and rerun calibration while research remains stopped.
- Use the measured allowance delta and stage telemetry to choose the next optimization target and bounded end-to-end calibration before any sustained START.
- After monitoring/tuning is validated, continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Lambda local research-engine main@051a3b0c9828de411812b0a519a070a2aa87683b is behind validated remote main@774b2cb5d8a99b9edd5238c6ca83383a6be30add; daemon remains intentionally stopped.
- A second trustworthy 5-hour/weekly observation interval is still required to estimate allowance burn; the one-call VERIFY replay runner is designed to create that interval safely.
- Sustained START remains gated on calibration outcome: VERIFY result agreement must be reviewed and allowance/token reduction measured.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
