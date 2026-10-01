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
- Remote checkpoint: 051a3b0c9828de411812b0a519a070a2aa87683b
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 263a9dfb2d22b31922647e129ae32f0d6aa1f7e0
- Local clean: true

## Current stage

hud_and_ops_cli

## Next safe action

On the Lambda while research-engine-daemon.service remains inactive/dead, clean fast-forward research-engine main from 263a9dfb2d22b31922647e129ae32f0d6aa1f7e0 to exact validated 051a3b0c9828de411812b0a519a070a2aa87683b. Do not rerun schema migration and do not START. Because the venv is an editable install, immediately run `HUD --once --no-color` and return the PIPELINE, AGENTS, USAGE / EFFICIENCY, USAGE BY STAGE, QUEUE / ALERTS, and allowance sections for tuning review.

## Remaining work

- Fast-forward the paused Lambda to research-engine main@051a3b0c9828de411812b0a519a070a2aa87683b and capture HUD --once --no-color; confirm run-scoped evidence and historical Luna/Terra/Sol labels plus the new usage-by-stage panel.
- Analyze stage-level historical usage for the completed 9-paper sustained batch (28 semantic calls, 959229 input tokens, 22030 output tokens) and design a tightly bounded calibration workload.
- Take a second 5-hour/weekly allowance reading immediately around that bounded calibration workload and use the measured allowance delta to tune model/tier/concurrency/context/fanout before any sustained START.
- After monitoring/tuning is validated, continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Lambda is one code-only fast-forward behind canonical research-engine main: local 263a9dfb2d22b31922647e129ae32f0d6aa1f7e0 versus validated remote 051a3b0c9828de411812b0a519a070a2aa87683b. No schema migration is required for this HUD accuracy patch.
- At least two trustworthy timestamped observations in the same Codex allowance window are required before exhaustion ETA can move beyond CALIBRATING.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
