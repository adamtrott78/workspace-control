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
- Remote checkpoint: 50d5a5cf032721c81e6a8a14060514002d2b48da
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 4d6a3bf003499a34ea0d076e55c724aaf1735c42
- Remote verified: true

## Next safe action

Create an inert trigger PR from exact implementation research-engine@4d6a3bf003499a34ea0d076e55c724aaf1735c42, checkpoint its exact head SHA, and issue exactly one owner comment `/local-extract-obligation-validity-microbenchmark <SHA>`. Do not change frozen science. Stop on the first integrity-valid result, checkpoint it, and hand it to the independent reviewer. No acceptance freeze or sealed holdout access.

## Remaining work

- Create an inert trigger PR from research-engine@4d6a3bf003499a34ea0d076e55c724aaf1735c42 with no scientific changes.
- Checkpoint the exact inert trigger SHA and issue exactly one owner comment: /local-extract-obligation-validity-microbenchmark <exact_sha>.
- Wait for the exact one-shot development run; do not tune or rerun after an integrity-valid result.
- Capture run/job/artifact/report identities, scientific outcome, per-arm gates, completeness outcomes, and preservation/integrity evidence.
- STOP after the genuine result and re-engage independent reviewer before any next scientific phase.
- Keep acceptance_candidate_frozen=false and sealed semantic acceptance benchmark untouched.

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
