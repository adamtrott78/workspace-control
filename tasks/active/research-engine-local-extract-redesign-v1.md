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
- Remote checkpoint: e640116db885dcfc715e0ed5c5f3a029572763fb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: trigger-obligation-validity-microbenchmark-v1
- Remote checkpoint: a901115fb572a0647e70f87c39309bcda60f1dee
- Remote verified: true

## Next safe action

Issue exactly one owner comment `/local-extract-obligation-validity-microbenchmark a901115fb572a0647e70f87c39309bcda60f1dee` on research-engine PR #268. If the resulting execution has valid experiment integrity, stop on that result with no tuning or rerun, checkpoint exact run/job/artifact/report evidence, and hand it to the independent reviewer. No acceptance freeze or sealed holdout access.

## Remaining work

- Issue exactly one owner comment `/local-extract-obligation-validity-microbenchmark a901115fb572a0647e70f87c39309bcda60f1dee` on research-engine PR #268.
- Observe the exact one-shot run. If experiment integrity is valid, do not rerun regardless of scientific outcome or ordinary bad verifier outputs.
- Capture run/job/artifact/report identities, hashes, per-arm case outcomes, completeness simulation, preservation controls, and mechanism_outcome.
- Checkpoint the genuine result in workspace-control.
- STOP and re-engage the independent reviewer before any next scientific phase.
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
