<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Return to first principles on research-engine EXTRACT and identify, benchmark, and if justified implement a provenance-preserving mostly-local extraction architecture that makes STANDARD Codex a rare ambiguity/failure fallback rather than the default, while reusing accepted local document/VERIFY infrastructure and not repeating approaches already invalidated by durable evidence.

## Workflow

- Repository: workspace-control
- Path: workflows/evidence-first-solution-research.v1.json
- Checkpoint: a9041372c50bf1258daea2236a3e62542a115117

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ad4f788890473add0ca86bbcd5ca9de678dba75f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8329f160a154d86f8178bb094e9b53a8274193b5
- Remote verified: true

## Next safe action

Monitor exactly one active reranker bakeoff run 39983057391 from inert research-engine PR #159 at exact head 8329f160a154d86f8178bb094e9b53a8274193b5. Do not trigger another run while it is queued/running. If it reaches scientific scoring, recover and checkpoint the report, classify only under the frozen PROMISING/NEGATIVE rule, close PR #159 unmerged, and STOP before Wave 7. If it fails before producing any proposition score, classify the pre-scoring failure and fix only that runtime boundary before any retry.

## Remaining work

- Monitor run 39983057391 only; no duplicate trigger while it is queued or running.
- If the run produces valid arm rankings, recover the artifact and classify under the frozen PROMISING/NEGATIVE gate; do not retune queries, top_k, candidate pool, hybrid weights, support oracle, or thresholds after seeing results.
- If the run fails before any proposition score is produced, record that the scientific gate remains unconsumed and fix only the narrow pre-scoring runtime fault.
- After a valid result, checkpoint the report, close inert PR #159 unmerged, and stop before Wave 7 or any production EXTRACT/VERIFY change.
- Heartbeat executor-touch liveness remains an independent workspace-heartbeat task; v0.4.7 exposes heartbeat_touch but the canonical procedures/progress_heartbeat.md still lacks a touch-emission cadence/rule.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
