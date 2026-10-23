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
- Remote checkpoint: b08f0367095cc392352e44b50142c03ac51b2e5f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8e3481c4ad00ffe26cd175d0e6c6275081d70ab0
- Remote verified: true

## Next safe action

Exactly one Wave 7A.3 run is authorized from exact research-engine SHA 8e3481c4ad00ffe26cd175d0e6c6275081d70ab0 after trusted route reconciliation PASS run 40021083789. Create an inert open same-repository trigger PR at that exact head, issue one `/lambda-ci-local-extract-wave7a3 8e3481c4ad00ffe26cd175d0e6c6275081d70ab0` comment, then hard-stop at the frozen WAVE7A3_PROMISING/PARTIAL/REJECT verdict. Do not retune the contract, start Wave 7B, or change production EXTRACT/VERIFY.

## Remaining work

- Trigger exactly one Wave 7A.3 run from exact research-engine SHA 8e3481c4ad00ffe26cd175d0e6c6275081d70ab0 using the trusted /lambda-ci-local-extract-wave7a3 route.
- Apply only the frozen WAVE7A3_PROMISING / WAVE7A3_PARTIAL / WAVE7A3_REJECT gates, including explicit recovery of the six source-aware-BM25 residual teacher atoms and retention of prior supported atoms.
- Persist the exact run/artifact/report identities and scientific disposition in research-engine, close the inert trigger PR unmerged, and checkpoint workspace-control.
- Hard-stop before Wave 7B or production EXTRACT/VERIFY changes.
- Only if Wave 7A.3 rejects, reopen targeted design research for a trained scientific contribution/discourse classifier as a new independent variable; do not add it to the current experiment after seeing results.

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
