<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-research-knowledge-ontology-review-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-research-knowledge-ontology-review-v1
- Title: Research Knowledge Ontology Independent Review v1
- Status: COMPLETE
- Capsule schema: v2
- Disposition: **BLOCKING_FINDING**

## Exact reviewed target

- workspace-control checkpoint: `706957531271486b7df510933297fa9169134a65`
- owner task blob: `f7d88f4d94b498aa5eb847d06aca8e765d7813bc`
- ontology design: `architecture/research-knowledge-ontology.v0.1.json@9af5bea619ec5a2f83575b4c8d73d08922f05bdb`
- blind replay benchmark: `benchmarks/research_knowledge/research-state-replay-benchmark.v0.1.json@45bd39a722fc4ec24c8f29ce6c1d4eacda8c7998`

## Accepted design surfaces

The core ontology authority model is acceptable:

- epistemic state is non-executable;
- normative/scientific authority is source-derived only;
- execution state is observational;
- `CandidateAction` has no authority;
- `DecisionEvaluation` may authorize execution only through an external authority-owned policy/task evaluator;
- stale/superseded assertions remain historical and lower-precedence/open-PR state cannot override the current merged authoritative task state;
- preregistered verdicts, posthoc non-verdict evidence, validation unavailable, blocked evidence, and rejected-mechanism reopening are represented as distinct concepts.

## Blocking findings

1. **INVALID_EXECUTION is not non-vacuously tested.** The 16 cases include `VALID_NEGATIVE_SCIENCE`, `VALIDATION_UNAVAILABLE`, and `BLOCKED_EVIDENCE`, but no case expects `INVALID_EXECUTION`. An implementation that never emits `INVALID_EXECUTION` can still satisfy the current zero-conflation metric.

2. **Contradiction preservation is untested and its gate is missing from benchmark pass criteria.** No replay case contains coexisting contradictory assertions. The design requires `contradiction_silent_collapse_count_required=0`, but the benchmark pass criteria omit it. A projection that silently collapses contradictions can pass all 16 cases.

3. **A required query family is uncovered.** The design requires `WHY_CURRENT_EXPERIMENT`, but the frozen replay contains zero cases from that family. A missing or incorrect implementation can pass the benchmark.

4. **The blind boundary does not operationally prevent benchmark-specific hardcoding.** Every query-engine-visible tuple (`query_family` + structured `query_input`, including `target_id` and `ask`) is fixed and unique. A lookup keyed by those visible fields can reproduce the expected outputs without reading case IDs or gold at runtime. The current `no_case_specific_logic` declaration has no frozen executable anti-hardcoding/metamorphic/identifier-remapping or equivalent detection rule.

5. **Exact model-free scoring is not frozen.** Cases provide `expected_answer_class` plus natural-language `required_points` / `forbidden_claims`, but there is no deterministic comparison/canonicalization rule. Therefore `model_free_primary_scoring=true` and `16/16 exact` do not yet define a reproducible preregistered pass/fail function.

## Authority consequence

**No implementation authority exists from the reviewed blobs.** The owner must revise only the result-affecting contract surfaces needed to close the findings, freeze new exact design/benchmark blobs, and obtain a new independent review. This reviewer lane must not implement the projection or mutate the owner ontology/design/benchmark.

## Next safe action

Return `BLOCKING_FINDING` to the owner. Do not implement. After corrected exact blobs are frozen, re-engage an independent reviewer against those exact identities.

## Prohibited actions remain unchanged

Do not mutate Local EXTRACT, inspect the sealed semantic acceptance benchmark, change semantic-control integration, change policy/production behavior, or infer executor authority from graph state.
