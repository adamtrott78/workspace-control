<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-research-knowledge-ontology-rereview-v02.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-research-knowledge-ontology-rereview-v02
- Title: Research Knowledge Ontology v0.2 Independent Re-review
- Status: COMPLETE
- Capsule schema: v2
- Disposition: **BLOCKING_FINDING**

## Exact reviewed target

- workspace-control checkpoint: `61830a8ff473671112e2d866c5aaf41e503febf2`
- owner blob: `416e0c5b9ac6ce73cb34e8c86a0059a6622d67db`
- design: `architecture/research-knowledge-ontology.v0.2.json@039fd2f888fb1abfb663c841df3425e2aa69fb74`
- benchmark: `benchmarks/research_knowledge/research-state-replay-benchmark.v0.2.json@c73f6f531a05386c1177a2709690ad2b06739ea9`

Prior v0.1 review:
`workspace-control@706957531271486b7df510933297fa9169134a65|design@9af5bea619ec5a2f83575b4c8d73d08922f05bdb|benchmark@45bd39a722fc4ec24c8f29ce6c1d4eacda8c7998:BLOCKING_FINDING`

## Re-review results

The already-accepted authority architecture remains sound:

- epistemic state remains `NON_EXECUTABLE`;
- normative/scientific authority remains `SOURCE_DERIVED_ONLY`;
- execution state remains `OBSERVATIONAL`;
- `CandidateAction` has authority `NONE`;
- executable permission still requires the external authority-owned evaluator.

The correction also genuinely closes important parts of the prior review:

- active contradiction and resolved/superseded contradiction are paired under identical query visibility;
- `contradiction_silent_collapse_count=0` is restored;
- all 10 required query families are covered, including `WHY_CURRENT_EXPERIMENT`;
- canonical scoring removes natural-language/fuzzy grading and freezes duplicate rejection, raw UTF-8 sorting, exact equality, and no repair/retry.

## Blocking findings

1. **The positive INVALID_EXECUTION control is not graph-self-sufficient.** `R18A_SYNTH_VALID_EXECUTION` expects `VALID_NEGATIVE_SCIENCE` and `NEGATIVE_RESULT_REMAINS_SCIENTIFIC`, but `SYNTH_EXEC_VALID` contains only matching expected/observed design identity and `execution_integrity=VALID` (plus a distractor). There is no assertion that a scientific result is negative. The expected output therefore cannot be derived from the frozen visible graph alone. Add explicit negative-result evidence/provenance or narrow the expected output to what the graph establishes.

2. **Anti-hardcoding remains only partially operational.** Identifier relabeling changes `target_id` and graph identifiers, but leaves `query_family`, `target_kind`, `ask`, and `as_of_snapshot` unchanged. Across 21 base cases those fields form 19 signatures: only the two synthetic pairs share a signature; the other 17 are singleton fingerprints. A hybrid implementation can hardcode those 17 outputs and use graph semantics only for the two pairs, surviving both relabel variants. The frozen contract has no executable detection rule that makes such case-specific lookup fail across the benchmark.

3. **The design freezes two incompatible replay output schemas.** `bounded_query_contract.answer_contract` requires `answer_class, answer, supporting_assertion_ids, source_refs, authority_boundary, unproven_or_caveat` and says `model_free_replay_baseline=true`. `deterministic_scoring_contract.engine_output_schema` instead requires `answer_class, claim_codes, support_handles, authority_boundary, caveat_codes` and forbids additional fields. No precedence or translation boundary is frozen, so an implementation cannot satisfy both as written.

## Authority consequence

**No implementation authority exists from the reviewed v0.2 blobs.** The owner must correct only these result-affecting contract surfaces, freeze new exact design/benchmark blobs, and obtain another independent review.

## Next safe action

Return `BLOCKING_FINDING` to the owner. Do not implement. Correct the valid-control evidence, make anti-hardcoding operational across the benchmark rather than only the paired synthetic cases, and unify/freeze one replay query-engine output schema. Then freeze new exact blobs and re-review.

## Restrictions remain unchanged

No implementation. No owner/design/benchmark mutation from this reviewer lane. No Local EXTRACT mutation. No sealed acceptance benchmark access. No semantic-control integration, policy, routing, or production change.
