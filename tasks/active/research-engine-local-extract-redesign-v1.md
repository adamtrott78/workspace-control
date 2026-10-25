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
- Remote checkpoint: 87311dbb30fdd0ccc7b6f66c02ade9b4d26d1a78
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 15c2f98feb980f18fac255b74c6a39db5da4ef30
- Remote verified: true

## Next safe action

Do NOT trigger EXACT_PROVENANCE_BINDING_MICROBENCH_V1 yet. First obtain a successful trusted Lambda CI Project Reconcile source-validation run for the current workspace-control project manifest, allowing the live reconciliation controller to install cpu-validation-exact-provenance and model-eval-exact-provenance-binding. Then obtain an executed PASS receipt from validation run 40242535180 on research-engine PR #273 exact head 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d (or replace only if that queued run becomes unusable). Only after executed CPU validation PASS may the owner checkpoint the validated exact SHA and issue exactly one scientific trigger. No acceptance freeze or sealed holdout access.

## Remaining work

- Get a successful trusted Lambda CI Project Reconcile source-validation run for current workspace-control reconciliation inputs. Current zero-step GitHub-hosted failures do not count as validation or scientific failures.
- Let live reconcile-controller apply the cpu-validation-exact-provenance and model-eval-exact-provenance-binding routes.
- Obtain executed CPU implementation/contract validation PASS for exact inert PR #273 head 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d (or a new marker-only exact head only if the existing queued run becomes unusable).
- Do not issue any model/GPU scientific trigger before that PASS.
- After validation PASS, checkpoint the exact validated implementation/trigger SHA and issue exactly one /local-extract-exact-provenance-binding-microbenchmark <SHA> command.
- Stop on the first integrity-valid scientific result and re-engage the independent reviewer before selecting any next phase.
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
