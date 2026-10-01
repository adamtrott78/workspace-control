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
- Local HEAD: bd62520387daa03d9c1b0cc4ab2365ccda85631c
- Local clean: true

## Current stage

codex_allowance_telemetry_and_forecasting

## Next safe action

Keep research-engine-daemon.service inactive/dead. On the Lambda, verify the clean checkout is main@bd62520387daa03d9c1b0cc4ab2365ccda85631c, fetch and fast-forward only to canonical research-engine main@f2349313e069f4f121eb07713169a2edc77bf54d, then run bash deploy/run-verify-ab-batch.sh job:7b6ca4026f026bedaec4859e 3. Provide one complete pasted 5-hour+weekly usage block before radius 0, one between the radius-0 and radius-1 phases, and one after radius 1. Preserve the complete output. The batch is six STANDARD/Terra calls total, non-materializing, and must finish with the daemon inactive/dead. Do not START sustained research.

## Remaining work

- Keep research-engine-daemon.service inactive/dead. Fast-forward the clean Lambda main checkout from bd62520387daa03d9c1b0cc4ab2365ccda85631c to canonical f2349313e069f4f121eb07713169a2edc77bf54d.
- Run bash deploy/run-verify-ab-batch.sh job:7b6ca4026f026bedaec4859e 3. Paste one fresh complete usage-limit block before the radius-0 phase, one after radius 0 / before radius 1, and one after radius 1. This performs six STANDARD/Terra calls total and must end daemon inactive/dead.
- Compare radius-0 vs radius-1 agreement rates across the three repeated calls per radius and exact replay input/cached/output/reasoning distributions. Use the phase-level censored UI deltas only for average plan-allowance mapping, not exact per-call percentages.
- If radius 0 repeatedly preserves accepted IDs, treat the original mismatch as likely stochastic and retain radius 0 for the next bounded production calibration. If radius 0 repeatedly disagrees while radius 1 is stable, prefer a safer context policy or investigate a narrower targeted-context alternative before sustained production.
- Do not implement global page-selective EXTRACT from current evidence and do not resume sustained corpus expansion yet.
- After tuning is validated, continue the Chat-visible ops mirror, private MCP direct-tool surface, and Slack wake-up/reasoning bridge.

## Blockers / gates

- A single radius-0 high-cost replay failed accepted-evidence-ID equality while a single radius-1 replay passed. One sample at each radius cannot distinguish a stable context-window effect from stochastic verifier variation.
- The whole-percent plan UI is too coarse for precise per-call allowance attribution. Repeated phase-level calls are required to narrow batch-average plan-consumption bounds.
- EXTRACT evidence spans 43/65 pages across the preserved corpus, so a global page-selective EXTRACT policy remains unjustified.
- Sustained START remains gated on the repeated VERIFY A/B stability/allowance experiment and the resulting smallest-safe context policy.

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
