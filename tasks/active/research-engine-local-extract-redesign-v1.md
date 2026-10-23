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
- Remote checkpoint: 4b2c56eebe6ce7f04320f6ae31d11754f9eda197
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 265a7e4784209d411383cb09da4fe0adcf50f319
- Remote verified: true

## Next safe action

STOP at the Wave 6 checkpoint. The one authorized benchmark is complete and inert research-engine PR #141 is closed unmerged. Wave 6 remains scientifically PARTIAL: selector alignment reached the intended 0.30305743036333815 target, but local completion is 8/9 and teacher coverage at F1>=0.5 remains 0/6. Do not start Wave 7 automatically. Production EXTRACT remains STANDARD Codex and accepted Qwen VERIFY remains unchanged. Resume only after an explicit decision selects a residual-focused next experiment or ends the redesign.

## Remaining work

- Do not automatically design, implement, route, or execute Wave 7.
- Treat the Wave-6 selector hypothesis as confirmed: paper-global BM25 reached the intended 0.30305743036333815 selected-source mean F1, but the end-to-end candidate remains PARTIAL because one paper required residual fallback and normalized semantic agreement remains below the promotion gate.
- Any further experiment requires an explicit new decision that names the residual being tested; production EXTRACT remains STANDARD Codex and accepted page-scoped Qwen VERIFY remains unchanged.
- If work resumes, analyze the two CLAIM_SCHEMA normalization rejects on arxiv:2609.20765 and the persistent 0/6 teacher coverage before selecting a next bounded experiment; do not reopen GitRunner/controller/provisioner/runtime design.

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
