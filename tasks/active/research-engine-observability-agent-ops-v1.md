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

## Current stage

chat_reasoning_bridge

## Next safe action

Do not START sustained research from this task. The Chat-visible ops mirror is validated through GitHub issue #32. Pause substantive Slack/Chat reasoning-bridge implementation while the sibling task tasks/active/research-engine-local-document-pipeline-v1.json benchmarks local document intelligence and whole-pipeline offload. When that task produces measured residual remote-reasoning demand, return here to decide the smallest useful bridge surface (likely exception/human-review wakeups rather than routine research throughput).

## Remaining work

- Keep the Chat-visible issue publisher available as the current read-only operational surface; choose/update cadence only when sustained research resumes.
- Defer substantial Slack/Chat reasoning bridge implementation until research-engine-local-document-pipeline-v1 benchmarks document/local offload and re-estimates the residual need for remote high-level reasoning.
- When bridge work resumes, use Slack only as a wake-up/request transport and GitHub/PostgreSQL as durable audit/authority; advisory Chat responses must not directly mutate scientific state.
- Evaluate/implement the private research-engine MCP/direct-tool surface for bounded ops reads and advisory request/response submission after the local-compute architecture stabilizes.
- Perform live runtime validation of the combined ops mirror + deferred/selected bridge path before completing this task.

## Blockers / gates

- The Chat-visible ops mirror stage is validated end-to-end; no mirror blocker remains.
- Slack/Chat reasoning bridge implementation is intentionally deferred behind research-engine-local-document-pipeline-v1 because measured throughput is dominated by EXTRACT/VERIFY document processing.
- Sustained START remains gated by the broader automated-research-engine control plane and pending human review; this task does not authorize restart.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-observability-agent-ops-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
The Chat-visible ops mirror is already validated through research-engine issue #32.
Substantive Slack/Chat reasoning-bridge implementation is intentionally deferred behind tasks/active/research-engine-local-document-pipeline-v1.json.
Do not START sustained research from this task.
