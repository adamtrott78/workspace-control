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
- Remote checkpoint: f2349313e069f4f121eb07713169a2edc77bf54d
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: f2349313e069f4f121eb07713169a2edc77bf54d
- Local clean: true

## Current stage

chat_visible_ops_mirror

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. With research-engine canonical and Lambda both at main@f2349313e069f4f121eb07713169a2edc77bf54d, implement and CI-validate the Chat-visible ops mirror GitHub-side first: a bounded derived snapshot/Markdown publisher suitable for one machine-maintained GitHub issue plus low-frequency durable rollups, with no prompts/source text/secrets and no scientific-state mutation. Do not assume Lambda GitHub credentials; after repository-side CI passes, validate the publication mechanism on Lambda separately. Continue afterward toward the private MCP direct-tool surface and Slack wake-up/advisory bridge.

## Remaining work

- Implement the Chat-visible ops mirror as a derived, bounded operational surface. Raw high-frequency truth remains PostgreSQL-authoritative; do not use workspace-control main or canonical research-engine commits as a high-frequency telemetry sink.
- Prefer one machine-maintained GitHub issue for current state plus low-frequency permanent daily/run rollups. The mirror must expose daemon/run/phase, agents/jobs, queue/evidence/gap funnels, throughput, failures/backoffs, usage by tier/model/job type, and censored allowance status without prompts/source text/secrets.
- Validate the Lambda-side publication mechanism and credentials separately; do not assume GitHub CLI/token availability. Publisher failure must not stop scientific processing.
- Evaluate/implement the private research-engine MCP/plugin direct-tool surface for reading bounded ops state and submitting advisory responses, validating actual plan/workspace permissions rather than assuming writes.
- Then implement/evaluate the Chat reasoning bridge with GitHub durable audit and Slack as the first candidate wake-up transport; advisory responses must not directly mutate scientific state.
- Keep sustained corpus expansion paused until chat-visible mirror/bridge work reaches live-runtime validation. Retain VERIFY radius 0 for the next bounded production calibration.

## Blockers / gates

- Sustained START remains gated. The tuning decision is complete, but the Chat-visible ops mirror and advisory reasoning bridge still need implementation/validation before live runtime validation.
- The whole-percent plan UI supports only censored batch-level allowance calibration; exact token-to-plan conversion remains intentionally unidentified.
- EXTRACT evidence spans 43/65 pages across the preserved corpus, so global page-selective EXTRACT remains unjustified.

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
