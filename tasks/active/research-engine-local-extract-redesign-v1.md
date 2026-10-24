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
- Remote checkpoint: 3450afdff207bc4fdccf6db79ef790dba6a0de83
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 3f433e3e31fd8fac3edf86f65cef9628635652cf
- Remote verified: true

## Next safe action

Implement NONDESTRUCTIVE_EVIDENCE_FRONTIER_DIAGNOSTIC_V1 exactly from frozen design research-engine@3f433e3e31fd8fac3edf86f65cef9628635652cf. Add only the deterministic append-only diagnostic runner/tests and any bounded workflow/fixture wiring needed to replay frozen inputs; do not change selector, budgets 24/26/28/32, controls, evaluator, verdict interpretation, models/prompts, production EXTRACT/VERIFY, or teacher-blind boundary.

## Remaining work

- Implement NONDESTRUCTIVE_EVIDENCE_FRONTIER_DIAGNOSTIC_V1 exactly as frozen in research-engine, with deterministic tests and no generation/model changes.
- Run normal CI and persist the exact implementation checkpoint before scientific execution.
- Execute exactly one scientific diagnostic and stop at ADDITIVE_FRONTIER_CONFIRMED/PARTIAL/NEGATIVE; no valid-result rerun or tuning.
- After the genuine result, obtain independent post-result review before selecting the next scientific phase.
- Do not reopen rejected NLI/predicate-argument/AMR mechanisms, alter production EXTRACT/VERIFY, start Wave 7B, or emit semantic-control/RDF/ontology output.

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
