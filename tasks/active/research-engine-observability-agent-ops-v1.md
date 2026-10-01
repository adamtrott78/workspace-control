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
- Remote checkpoint: 02453b856fbb6d5cac8e611949579a61822560f4
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 6a423e0fd38283687cae2eb060405a2a82643450
- Local clean: true

## Current stage

hud_and_ops_cli

## Next safe action

Run the fail-closed paused-Lambda HUD deployment script against exact research-engine main@02453b856fbb6d5cac8e611949579a61822560f4. It must require research-engine-daemon.service to remain inactive/dead, require a clean fast-forward main checkout, initialize the additive schema, verify observability tables/columns and preserved scientific run state, optionally record current timestamped 5-hour/weekly allowance observations supplied interactively by the user, generate an ops-snapshot and one-shot HUD for rf-open-world-corpus-expansion-v1, install a convenient research-hud wrapper, and finish with the daemon still stopped. Do not resume semantic processing yet.

## Remaining work

- Fast-forward the paused Lambda checkout to research-engine main@02453b856fbb6d5cac8e611949579a61822560f4 without restarting research.
- Initialize the additive observability schema and audit historical worker/usage backfill against the existing acceptance and sustained-run records.
- Record current timestamped 5-hour and weekly Codex allowance readings from the ChatGPT UI; do not treat the earlier approximate 16% reading as a precisely timed forecast sample.
- Validate ops-snapshot and the one-shot/live terminal HUD against rf-open-world-corpus-expansion-v1 while the daemon remains stopped.
- After the HUD is trusted, collect a second allowance reading around a tightly bounded calibration workload and tune model/tier/concurrency budgets before sustained research resumes.
- Then continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Lambda is intentionally still deployed at research-engine main@6a423e0fd38283687cae2eb060405a2a82643450 with research-engine-daemon.service inactive/dead; observability main@02453b856fbb6d5cac8e611949579a61822560f4 must be fast-forward deployed and the additive schema initialized before the live HUD can be validated.
- At least two trustworthy timestamped observations in the same Codex allowance window are required before exhaustion ETA can move beyond CALIBRATING.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
