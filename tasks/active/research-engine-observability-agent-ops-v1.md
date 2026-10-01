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
- Remote checkpoint: 6a423e0fd38283687cae2eb060405a2a82643450
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 6a423e0fd38283687cae2eb060405a2a82643450
- Local clean: true

## Current stage

observability_contract

## Next safe action

With research-engine-daemon.service confirmed inactive/dead and rf-open-world-corpus-expansion-v1 preserved, inspect the existing research_workers, research_jobs, research_job_attempts, research_usage_events, daemon health/report code, Codex execution metadata, and deployment/runtime identifiers. Write and validate the observability contract first: stable logical agent roles versus ephemeral sessions, append-only telemetry fields, derived metric formulas/windows, retention policy, allowance-observation/forecast semantics, HUD panel contract, Chat-visible summary contract, and MCP/Slack request-response safety boundary. Then implement the read-only ops snapshot and terminal HUD without resuming semantic processing.

## Remaining work

- Pause the research-engine user daemon on the Lambda, preserving rf-open-world-corpus-expansion-v1 durable state and preventing further semantic allowance burn during instrumentation.
- Specify the metric taxonomy, stable logical-agent identity, event/rollup schema, retention policy, and exact separation between authoritative PostgreSQL telemetry and derived views.
- Implement read-only ops snapshot/report commands and a terminal HUD first, including live per-agent usage, source/evidence/gap throughput, queue/latency, failures/backoffs, and 5-hour/weekly allowance panels.
- Implement explicit 5-hour/weekly Codex usage observations plus empirical forecast calibration/ETA with uncertainty and per-agent/model attribution; ingest the current ~16% 5-hour observation as the first calibration point.
- Run a tightly bounded monitored calibration workload and tune model/tier/concurrency budgets before resuming sustained corpus expansion.
- Implement a low-frequency Chat-visible operations mirror.
- Prototype a private research-engine MCP/plugin as the preferred direct ChatGPT read/advisory-response surface; validate current-plan permissions and Secure MCP Tunnel or another private transport.
- Optionally connect Slack and evaluate it as an event-driven reasoning-request wake-up bus; retain GitHub/PostgreSQL as durable truth.
- Implement and validate structured Chat reasoning request/response state transitions without allowing Chat responses to bypass scientific verification or human gates.

## Blockers / gates

- Direct MCP/plugin write capability and any Slack-triggered automation must be validated on the user's actual ChatGPT plan/workspace before the bridge can depend on them.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
