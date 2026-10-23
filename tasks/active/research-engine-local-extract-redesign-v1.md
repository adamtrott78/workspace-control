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
- Remote checkpoint: 2f5b950c557171318e5cb764add35fc3c95a97fc
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 80da2cae9f8d80a7e7049a9b5339807becc54a98
- Remote verified: true

## Next safe action

STOP at the valid Wave 7A.3 scientific checkpoint. Run 40027366528 is implementation-valid and WAVE7A3_REJECT; the scientific gate is consumed, PR #178 is closed unmerged, and Wave 7B is not authorized. Do not issue another Wave 7A.3/Wave 7B trigger or tune the frozen experiment. If the user explicitly resumes local EXTRACT research, begin a new evidence-first design phase for a materially different intent-generation architecture using benchmarks/document_intelligence/local-extract-wave7a3-author-anchored-result.v1.json as exclusion evidence.

## Remaining work

- No current experiment or Wave 7B execution is authorized after the valid WAVE7A3_REJECT.
- If the user explicitly resumes the local EXTRACT redesign, start a new evidence-first research/design phase that treats author-anchored obligations as rejected-as-implemented and requires a materially different intent-generation architecture before any new run.
- Preserve production STANDARD Codex EXTRACT and accepted page-scoped Qwen VERIFY unless a separate future task explicitly reopens those production boundaries.

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
