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
- Remote checkpoint: 34e475bd8480c85299aa5bd81441abf8adbc478c
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: dcdcfc8c85ddda2bfbf8fe439c79a8e0784ee276
- Remote verified: true

## Next safe action

Observe only research-engine Wave 7A.3 run 40027366528, created by the single authorized trigger comment 6375134209 at exact candidate SHA dcdcfc8c85ddda2bfbf8fe439c79a8e0784ee276. Do not issue any duplicate trigger. When terminal, recover its artifact and apply implementation validity before accepting any PROMISING/PARTIAL/REJECT scientific verdict; checkpoint the disposition immediately, then close PR #178 unmerged.

## Remaining work

- Observe unique corrected Wave 7A.3 run 40027366528 through terminal state; do not retrigger.
- Recover the generated-intents/report artifact and first apply the frozen implementation-validity gate. INVALID_IMPLEMENTATION leaves scientific_gate_consumed=false; PROMISING/PARTIAL/REJECT is the single valid scientific disposition.
- Checkpoint the run ID, artifact ID/hashes, implementation-validity evidence, control metrics, and scientific disposition immediately in research-engine and this task capsule.
- Close inert trigger PR #178 unmerged after result checkpointing. Do not begin Wave 7B and do not change production STANDARD Codex EXTRACT or accepted page-scoped Qwen VERIFY.

## Blockers / gates

- Wave 7A.3 corrected run 40027366528 is the unique in-flight scientific benchmark created by comment 6375134209. Do not issue any second /lambda-ci-local-extract-wave7a3 trigger under any circumstance; observe this run only.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
