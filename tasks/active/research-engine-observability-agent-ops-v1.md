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
- Remote checkpoint: 263a9dfb2d22b31922647e129ae32f0d6aa1f7e0
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 28e8a0904831f70e5689fbc8de75fc1fbc071f32
- Local clean: true

## Current stage

hud_and_ops_cli

## Next safe action

On the paused Lambda, clean fast-forward research-engine main from 28e8a0904831f70e5689fbc8de75fc1fbc071f32 to exact validated 263a9dfb2d22b31922647e129ae32f0d6aa1f7e0 and rerun deploy/deploy-hud-paused.sh. At the prompts, enter the ChatGPT usage UI values directly as percent LEFT and relative reset duration (for the current screenshot: 86 then '3h 20m', 96 then '5d 8h'). The deployer is additive/idempotent and must finish with the daemon still stopped.

## Remaining work

- Fast-forward the paused Lambda to 263a9dfb2d22b31922647e129ae32f0d6aa1f7e0 and rerun the repository-owned paused HUD deployer.
- Inspect the real one-shot HUD and historical usage attribution while research remains stopped.
- Collect a second allowance reading around a tightly bounded calibration workload and tune model/tier/concurrency budgets before sustained research resumes.
- Then continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- Lambda local research-engine is at 28e8a0904831f70e5689fbc8de75fc1fbc071f32 after the interrupted paused-HUD deploy; daemon remains stopped.
- Lambda must fast-forward to validated main@263a9dfb2d22b31922647e129ae32f0d6aa1f7e0 and rerun deploy/deploy-hud-paused.sh to finish allowance observation, snapshot/HUD validation, and shortcut installation.
- At least two trustworthy timestamped observations in the same Codex allowance window are required before exhaustion ETA can move beyond CALIBRATING.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
