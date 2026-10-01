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
- Remote checkpoint: 73697608e3ab179b7ed617b1833796cc47f679c2
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: f2349313e069f4f121eb07713169a2edc77bf54d
- Local clean: true

## Current stage

chat_visible_ops_mirror

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. On the Lambda, verify the research-engine checkout is clean on main@f2349313e069f4f121eb07713169a2edc77bf54d, fetch and fast-forward only to canonical main@73697608e3ab179b7ed617b1833796cc47f679c2, render the sanitized Markdown mirror locally with research-engine ops-mirror --run-id rf-open-world-corpus-expansion-v1 --format markdown, then check command -v gh and gh auth status --hostname github.com. If gh auth is ready, run bash deploy/publish-ops-mirror.sh current and preserve the output so ChatGPT can verify the GitHub issue directly. If gh is missing or unauthenticated, stop there and report that exact boundary. Keep the daemon inactive/dead throughout.

## Remaining work

- Keep research-engine-daemon.service inactive/dead. Fast-forward the clean Lambda research-engine main checkout from f2349313e069f4f121eb07713169a2edc77bf54d to canonical 73697608e3ab179b7ed617b1833796cc47f679c2.
- Render research-engine ops-mirror --run-id rf-open-world-corpus-expansion-v1 --format markdown locally and preserve/inspect the bounded output. This step requires no GitHub credentials and must not mutate scientific state.
- Check command -v gh and gh auth status --hostname github.com. If gh is missing or unauthenticated, stop at that boundary and obtain only the required operator install/auth action; do not invent or persist credentials.
- If gh auth is ready, run bash deploy/publish-ops-mirror.sh current, then verify the created/updated [ops] research-engine live state issue through direct GitHub tooling and confirm the remote body matches the sanitized mirror contract.
- After current-state issue publication is validated, choose a low-frequency rollup cadence and validate one rollup comment; do not use canonical Git commits as a telemetry sink.
- Then continue to the private research-engine MCP/direct-tool surface and the Slack wake-up/advisory reasoning bridge, keeping PostgreSQL/GitHub as durable authorities and responses advisory-only.
- Do not resume sustained corpus expansion until the mirror/bridge path reaches live-runtime validation.

## Blockers / gates

- Sustained START remains gated. The Chat-visible mirror is canonical but has not yet been rendered/published from the Lambda runtime or verified through the actual GitHub issue surface.
- Lambda GitHub CLI availability/authentication is intentionally unknown. Do not assume credentials or install a publication timer until gh auth is validated.
- The whole-percent plan UI remains censored; exact token-to-plan conversion is intentionally unidentified.
- Global page-selective EXTRACT remains unjustified by the 43/65 evidence-bearing-page audit.

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
