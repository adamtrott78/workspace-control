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
- Remote checkpoint: 6d6020b734a4b3e0564c6f3907acb6940781b070
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Re-verify research-engine PR #273 is OPEN, same-repository, and still exactly at head 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d. Then issue exactly one owner comment `/local-extract-exact-provenance-binding-microbenchmark 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d`. Do not issue a duplicate trigger. Capture the exact run/job/artifact/report identities and stop on the first integrity-valid scientific result for mandatory independent post-result review. Keep acceptance_candidate_frozen=false and the sealed semantic acceptance benchmark untouched.

## Remaining work

- Issue exactly one /local-extract-exact-provenance-binding-microbenchmark 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d owner command after re-verifying PR #273 exact head.
- Capture the resulting run/job/artifact/report identities and determine whether the execution is integrity-valid under the frozen experiment contract.
- Stop after the first integrity-valid scientific result and re-engage the independent reviewer before selecting any next scientific phase.
- Do not tune or rerun an integrity-valid result; no duplicate scientific trigger is authorized.
- Keep acceptance_candidate_frozen=false and the sealed semantic acceptance benchmark untouched.

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
