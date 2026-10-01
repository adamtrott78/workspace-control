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
- Remote checkpoint: 28e8a0904831f70e5689fbc8de75fc1fbc071f32
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 02453b856fbb6d5cac8e611949579a61822560f4
- Local clean: true

## Current stage

hud_and_ops_cli

## Next safe action

On the paused Lambda, require research-engine-daemon.service inactive/dead, clean fast-forward main from 02453b856fbb6d5cac8e611949579a61822560f4 to exact validated 28e8a0904831f70e5689fbc8de75fc1fbc071f32, then execute deploy/deploy-hud-paused.sh. Enter current 5-hour/weekly Codex usage readings if available. The deployer must preserve the research run/scientific state, install START/STOP/HUD/STATUS, render a one-shot HUD, and finish with the daemon still stopped. Do not use START until the historical usage/HUD output has been reviewed and a bounded calibration plan is chosen.

## Remaining work

- Fast-forward the paused Lambda from 02453b856fbb6d5cac8e611949579a61822560f4 to 28e8a0904831f70e5689fbc8de75fc1fbc071f32.
- Run deploy/deploy-hud-paused.sh; verify existing editable import or build-isolated fallback, initialize additive observability schema, audit protected research state, record current allowance observations, install START/STOP/HUD/STATUS, and render the real one-shot HUD.
- Keep research stopped after deployment; inspect the real historical usage attribution and HUD output before any START.
- Collect a second allowance reading around a tightly bounded calibration workload and tune model/tier/concurrency budgets before sustained research resumes.
- Then continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Lambda checkout was fast-forwarded by the failed first HUD attempt to 02453b856fbb6d5cac8e611949579a61822560f4, but the additive observability schema was not applied because that attempt failed earlier at an unnecessary pip reinstall.
- Lambda must fast-forward once more to canonical research-engine main@28e8a0904831f70e5689fbc8de75fc1fbc071f32 and run the repository-owned paused HUD deployer; daemon must remain inactive/dead.
- At least two trustworthy timestamped observations in the same Codex allowance window are required before exhaustion ETA can move beyond CALIBRATING.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
