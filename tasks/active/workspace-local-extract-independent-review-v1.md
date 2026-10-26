<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-independent-review-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-independent-review-v1
- Title: Local EXTRACT Independent Review v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: review_exact_provenance_binding_post_result

## Goal

Provide an independent, durable review/support lane for research-engine-local-extract-redesign-v1 while preserving a single EXTRACT scientific owner.

## Exact review target

- Reviewed design: research-engine@13a129ef820c611adf6a6ca70598df1e67d56efc
- Design blob: 09603c4d65114c75ad3e112a357ee45da384f63e
- Experiment: EXACT_PROVENANCE_BINDING_MICROBENCH_V1
- Candidate: research-engine PR #273 @ 3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d
- Implementation validation: run 40269453984 / job 121398888450 / artifact 12626998979 / 31-of-31 contract tests PASS
- Scientific trigger: comment 6428625881, exactly once
- Scientific run: 40411159582 / job 121881887321 / SUCCESS
- Scientific artifact: 12693836542
- Artifact ZIP SHA256: 5094ba5d8c6b98c19f52cffa1aa1a814c953c991c18c5924db9802cc53464743
- Report SHA256: fce8c958e0f91dffd9a740de2c71d1d451c6e3861e399f1afa550a50bd8f4f24
- Frozen reported verdict: EXACT_PROVENANCE_BINDING_PREMISE_REJECTED

## Result summary to audit, not rewrite

- Arm A: 7/7 case contracts; rejects/abstains 3/3 false positives; accepts 3/4 true supports; 3/4 true supports have exact provenance; precision_first_pass=false.
- Arm B: 6/7 case contracts; rejects/abstains 3/3 false positives; accepts 4/4 true supports with exact provenance 4/4; sole contract failure is FP_TRAINING_PRETRAINING_NO_LABELS / INVALID_ENUM_OR_FIELD_TYPE; precision_first_pass=false.
- All experiment-integrity checks PASS.
- Evidence set unchanged 28 -> 28.
- Prior supported retention 9/9; frozen-control retention 7/7.
- 14 stateless model calls; no external model downloads.
- sealed_acceptance_benchmark_accessed=false; acceptance_candidate_frozen=false; production_routing_changed=false; wave7b_started=false.

## Next safe action

Perform the mandatory independent post-result review. Verify whether the frozen all-or-nothing gate requires EXACT_PROVENANCE_BINDING_PREMISE_REJECTED, characterize the Arm A and Arm B failures without posthoc gate changes, and persist NO_BLOCKING_FINDING or exact blocking findings in this reviewer task. Then return control to research-engine-local-extract-redesign-v1.

No rerun, retuning, acceptance freeze, sealed-holdout access, production EXTRACT/VERIFY change, Wave 7B, or semantic-control coupling is authorized.

## Fresh-chat initialization

@GitHub @Heartbeat

https://github.com/adamtrott78/workspace-control

Continue the durable independent-review task defined by:

`tasks/active/workspace-local-extract-independent-review-v1.json`

Task ID:

`workspace-local-extract-independent-review-v1`

Start from the normal `workspace-control` root route.

Treat the authoritative reviewer capsule, its synchronized Markdown handoff, exact durable Git state, owner EXTRACT capsule, and referenced run/artifact evidence as the complete handoff.

Do not rely on previous conversation state.

Immediately use Workspace Heartbeat with the same real task ID:

`workspace-local-extract-independent-review-v1`

Follow the capsule's `next_safe_action`.

Do not rerun or tune the scientific experiment. Do not mutate research-engine or the owner EXTRACT capsule. Persist only the independent review disposition and bounded findings in the reviewer capsule/handoff, then hand authority back to `research-engine-local-extract-redesign-v1`.
