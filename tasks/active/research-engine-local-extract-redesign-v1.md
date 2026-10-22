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
- Remote checkpoint: 87e736740169985ff17c8225d1c83b615a3b62dc
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Bind the exact merged Wave-2 workflow blob cb7fd59bcb6f857bd6148ecbc7e2eb320dc9a1fb to a new research-engine route model-eval-local-extract-wave2 using the already-accepted model-dual-public-v1 contract, with exact qwen3.5-4b/runtime bindings and the existing same-repository PR/actor gates. Validate and merge only the declarative manifest/test delta, require the trusted reconciliation path to accept/install that exact state, then trigger exactly one bounded Wave-2 benchmark. Do not modify controller/provisioner/runtime/reconciler code.

## Remaining work

- Localize Wave-1 failure into claim proposal/atomicization/guard semantics versus retrieval residuals using the recovered per-paper artifact evidence.
- Design the smallest materially different Local Evidence Agent iteration that avoids whole-paper rejection from local region fanout while preserving exact grounding, bounded claim counts, type semantics, and fail-closed unknown candidate IDs.
- Keep FACET_INTERLEAVED_BM25_V1 fixed for the first semantic iteration so claim-generation effects are separable; only open retrieval changes against measured low-recall papers after semantic failure modes are isolated.
- Implement the new EXTRACT iteration in research-engine with no production routing change and no scientific materialization during benchmarking.
- Execute through the accepted reusable Git/Lambda runner and compare against the preserved nine-paper / 71-evidence-object Wave-1 baseline.
- Measure local completion, claim-level teacher agreement on the preserved teacher subset, provenance safety, fallback fraction, latency/resource use, and projected remote-token suppression.
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
