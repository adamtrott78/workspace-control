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
- Remote checkpoint: 78155d9bf8f0d0479e541f92d571b314f85b98e6
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 3bec68414a929ea82dc70e9c6729250bb566663f
- Remote verified: true

## Next safe action

Implement the external-only SCIENTIFIC_NLI_REDUNDANCY_CERTIFICATE_VALIDATION_V1 from research-engine@3bec68414a929ea82dc70e9c6729250bb566663f. The harness may download only the pinned tasksource/deberta-small-long-nli model revision and pinned SPARK/SciNLI validation data; it must not read EXTRACT teacher fixtures. Run normal CI, durable-checkpoint the validation implementation, then execute exactly one external validation run and record NLI_CERTIFICATE_VALIDATED/PARTIAL/REJECTED before any learned certificate is allowed into an EXTRACT experiment.

## Remaining work

- Implement the frozen external-only SCIENTIFIC_NLI_REDUNDANCY_CERTIFICATE_VALIDATION_V1 harness and hosted workflow.
- Validate pinned tasksource/deberta-small-long-nli revision/hash on external SPARK proposition-clustering data and held-out SciNLI entailment discrimination, using only the frozen calibration split/grid/gates.
- Checkpoint NLI_CERTIFICATE_VALIDATED/PARTIAL/REJECTED with exact model/data/run/artifact/report identities.
- Only if NLI_CERTIFICATE_VALIDATED may a separate EXTRACT design substitute the validated mutual-entailment certificate into the accepted dynamic-swap/page-preservation/top-24 architecture.
- Do not use EXTRACT teacher labels for NLI calibration, tune the accepted lexical 0.40 certificate post hoc, treat FEASIBLE as production promotion, start Wave 7B, alter production EXTRACT/VERIFY, or incorporate semantic-control/ontology mechanisms.

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
