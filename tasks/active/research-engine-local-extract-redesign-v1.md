<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: CHECKPOINTED
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
- Remote checkpoint: 1ff020ab832c729e9c830cbc5bcbd8fafe305f48
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5ab76baaa7f3be491780fc66f1d83104f70ef341
- Remote verified: true

## Next safe action

Merge this exact baseline-depth fallback pre-run checkpoint. Then issue exactly one `/local-extract-cross-paper-baseline-depth-fallback 36e0436bd88277b813396cdeb440f06c84aabb10` comment on research-engine PR #254 and bind the unique resulting run. Do not issue a second trigger.

## Remaining work

- After this exact checkpoint merges, issue exactly one `/local-extract-cross-paper-baseline-depth-fallback 36e0436bd88277b813396cdeb440f06c84aabb10` comment on research-engine PR #254.
- Bind the unique resulting run and inspect the uploaded baseline-only report.
- Stop at DEPTH_FALLBACK_COMPLETES_ALL_NINE / DEPTH_FALLBACK_STILL_INCOMPLETE / BASELINE_IDENTITY_REGRESSION; INVALID_EXECUTION is operational no-verdict. Do not tune/rerun after a valid result.
- Persist the exact result, close PR #254 unmerged only after result checkpoint is durable, and obtain independent post-result review.
- Do not run the recovery comparison yet; a COMPLETE result only authorizes a new corrected recovery-comparison design/review.

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
