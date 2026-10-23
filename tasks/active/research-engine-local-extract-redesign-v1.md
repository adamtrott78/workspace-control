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
- Remote checkpoint: fd40f6e9c7eb29f41067814bd0cc4853cd18433a
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 3c0ad3eefd70c86c0bfdc2349ac23d2d47022882
- Remote verified: true

## Next safe action

Resume at Wave 7A.3 implementation-validity repair, NOT research/design. Read research-engine benchmarks/document_intelligence/local-extract-wave7a3-invalid-interface.v1.json and the frozen Wave 7A.3 contract. Diagnose/fix only the author-anchor structured-output interface and add a hard generator-success validity gate; audit exact source-aware control representation/parity without changing the frozen scientific hypothesis, residual atoms, retrieval budget, PROMISING/PARTIAL/REJECT thresholds, model family, production EXTRACT, or VERIFY. The raw WAVE7A3_REJECT from run 40021544696 is INVALID_IMPLEMENTATION and the scientific gate remains unconsumed. Do not issue a new trigger until the repair is CI-valid (and route-reconciled if the workflow blob changes).

## Remaining work

- STOP after the Wave 7A.3 invalid-interface recovery; do not treat raw WAVE7A3_REJECT as scientific evidence and do not start Wave 7B.
- Do not redo the completed scientific-salience/contribution research or redesign the frozen Wave 7A.3 hypothesis/gates. The author-framed problem/contribution/result/limitation anchor architecture remains the experiment under test.
- Repair only Wave 7A.3 execution validity: diagnose why verdict-eligible anchor generation emits multiple/invalid JSON structures through the current model_claims interface, and make structured output reliably schema-conformant without tuning the scientific content toward teacher answers.
- Add a hard pre-scientific validity gate so the workflow/evaluator cannot emit PROMISING/PARTIAL/REJECT when the verdict-eligible generator fails closed across the required evaluation corpus; preserve diagnostics/artifact upload for invalid runs.
- Audit the source-aware control implementation against the exact valid Wave 7A.2 control representation and explain the BM25 5/13 versus frozen 7/13 drift before rerunning. Do not alter frozen promotion thresholds based on this observed run.
- Validate the bounded implementation repair in research-engine CI. If the trusted workflow blob changes, update only the declarative workspace-control route identity and pass trusted reconciliation; do not change controller/provisioner/GitRunner authority.
- After implementation validity is proven, create a fresh inert trigger PR at the corrected exact SHA and issue exactly one valid Wave 7A.3 run under the unchanged contract. Then checkpoint the scientific disposition and close the trigger unmerged.
- Keep production STANDARD Codex EXTRACT and accepted page-scoped Qwen VERIFY unchanged throughout.

## Blockers / gates

- Wave 7A.3 run 40021544696 is the unique in-flight scientific benchmark. Do not issue any second /lambda-ci-local-extract-wave7a3 trigger while it is queued or running.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
