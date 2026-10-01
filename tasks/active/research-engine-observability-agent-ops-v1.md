<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-observability-agent-ops-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-observability-agent-ops-v1
- Title: Research Engine Observability, Agent Operations & Chat Bridge v1
- Status: PLANNED
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

## Current stage

observability_contract

## Next safe action

Start from research-engine main at the verified launch checkpoint and inspect the existing research_workers, research_jobs, research_job_attempts, research_usage_events, daemon health/report code, Codex execution metadata, and current sustained-run runtime. Write the observability contract first: define stable logical agent roles versus ephemeral sessions, append-only telemetry fields, derived metric formulas/windows, allowance-observation/forecast semantics, GitHub live-ops issue format, daily/run rollup format, and chat-reasoning request/response safety boundary. Do not add telemetry schema or runtime mutation until that contract is explicit and regression-safe for the already-running rf-open-world-corpus-expansion-v1.

## Remaining work

- Specify the metric taxonomy, stable logical-agent identity, event/rollup schema, retention policy, and the exact separation between authoritative PostgreSQL telemetry and derived Chat-visible summaries.
- Extend usage/event capture to include cached input tokens, reasoning output tokens, wall/queue duration, agent/session attribution, error/backoff outcomes, and stage/source/evidence/gap throughput.
- Implement read-only ops snapshot/report commands and a terminal HUD with rolling throughput, queue/latency, source/evidence/gap funnel, current-agent, failure/backoff, and allowance panels.
- Implement explicit 5-hour/weekly Codex usage observations plus empirical forecast calibration/ETA with uncertainty and per-agent/model attribution.
- Implement a low-frequency GitHub live-ops issue publisher and permanent daily/run summaries that ChatGPT can read without high-frequency code commits.
- Implement structured Chat reasoning request/response records and a GitHub issue-based bridge; validate user-triggered Chat processing first, then separately evaluate an hourly ChatGPT automation if useful.
- Validate the complete observability stack against rf-open-world-corpus-expansion-v1 without interrupting or corrupting the running scientific workflow.
- Document operator commands and cold-start routes, then checkpoint and verify the implementation.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
