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
- Remote checkpoint: 60cd833271444eac862d45aa3dfbab68a8938a2c
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 265a7e4784209d411383cb09da4fe0adcf50f319
- Remote verified: true

## Next safe action

Bind merged research-engine Wave 6 into the existing reusable Lambda plane. Add route model-eval-local-extract-wave6 with execution contract model-dual-public-v1, trusted workflow .github/workflows/lambda-ci-local-extract-wave6.yml blob c81e7cbb31f1731ada483a9b1f9256a4e6d78312, trigger /lambda-ci-local-extract-wave6, unchanged actor/open-same-repository-PR/fork-denial gates, and accepted Qwen/runtime bindings. Advance only project-manifest source identity and exact-blob regression coverage, validate/merge, require trusted reconciliation, then execute exactly one inert-trigger Wave-6 benchmark. Do not modify GitRunner substrate code.

## Remaining work

- Freeze the Wave-6 paper-global proposition-ranking contract before implementation.
- Implement paper-global BM25 scoring over all propositions from the 12 selected regions, then retain the highest-scoring proposition per region; keep normalization unchanged.
- Fix the hard-safety evaluator so proposition lookup is scoped to the owning paper; preserve all other provenance guards.
- Validate/merge research-engine Wave 6, bind its exact launcher through the existing model-dual-public-v1 route pattern, reconcile, and run exactly one bounded benchmark.
- Immediately checkpoint the Wave-6 artifact and scientific disposition before any further experiment.
- Only after a candidate passes the semantic-quality gate consider VERIFY-boundary analysis or production integration.

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
