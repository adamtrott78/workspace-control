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
- Remote checkpoint: 4ad9d31dfd5297c176b99d5c67b7d795aa26cc09
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 54d347c248c7f9a8b9de9242abf01d082feb0bb5
- Remote verified: true

## Next safe action

Wave 5 implementation is merged in research-engine at 54d347c248c7f9a8b9de9242abf01d082feb0bb5 with workflow blob 2ef10f5b0940ff3c2238f74c0f0efbaf5bd61d6d. Install the already-reviewed Wave-5 declarative route using the existing accepted reusable execution contract, validate and reconcile it, then create one inert open trigger PR and run exactly one bounded Wave-5 benchmark. No reusable runner substrate changes are authorized.

## Remaining work

- Freeze a Wave-5 benchmark contract before implementation. Hold Wave-2 region construction, FACET_INTERLEAVED_BM25_V1 top-12 retrieval, exact proposition enumeration, Qwen normalization prompt/schema, strict guards, teacher scorer/F1 threshold, model/runtime/GPU topology, provenance rules, and production boundaries fixed.
- On research-engine branch local-extract-wave5-deterministic-proposal-ranking, replace only the Qwen proposition-selection call with deterministic per-region proposition ranking using the already-observed BM25 selector; preserve at most one selected proposition per region.
- Add diagnostics that separately report available-proposition ceiling, deterministic-selected proposition alignment, and final normalized teacher agreement so normalization can be adjudicated independently.
- Correct the Wave-5 launcher receipt assertions so they match Wave-5 metrics; do not rerun Wave 4 solely to repair its post-benchmark receipt assertion.
- Pass normal research-engine CI, merge the exact Wave-5 implementation, bind its exact launcher blob through the existing model-dual-public-v1 declarative route without GitRunner substrate changes, and require successful trusted reconciliation.
- Create one inert open same-repository trigger PR and execute exactly one bounded Wave-5 Lambda benchmark.
- At the Wave-5 result, immediately checkpoint exact run/artifact/report hashes, scientific decision, residual localization, and the next experiment before beginning any further wave.
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
