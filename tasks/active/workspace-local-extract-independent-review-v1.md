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

## Goal

Provide an independent, durable review/support lane for research-engine-local-extract-redesign-v1 while preserving a single EXTRACT scientific owner. Consume exact EXTRACT checkpoints, artifacts, benchmark/result evidence, and frozen gates; identify methodological or contract inconsistencies; assess downstream compatibility with the opaque semantic-control integration socket; and publish bounded review findings in workspace-control without changing EXTRACT science, implementation, acceptance criteria, or semantic-control production behavior.

## Repositories

### workspace-control
- Intent: mutate
- Remote branch: main
- Remote checkpoint: 013301d7d47d006de054a4ab5ee8082e693f5f09
- Remote verified: true

### research-engine
- Intent: read
- Remote branch: main
- Remote checkpoint: b939ff0bbb52024f55b2f6e719aef331f6286d06
- Remote verified: true

## Next safe action

Owner must correct OBLIGATION_VALIDITY_PRECISION_MICROBENCH_V1 before implementation: freeze exact model-visible obligation fields for each arm with fail_closed_conditions/evaluation labels excluded; freeze exact prompt/template and stateless case-isolation rules; freeze parsing/guard semantics so ordinary bad verifier outputs count against the arm rather than producing INVALID_EXECUTION/rerun authority. Then re-engage reviewer on the corrected exact SHA/blob. No implementation, acceptance freeze, or sealed holdout access before NO_BLOCKING_FINDING.

## Remaining work

- Wait for owner to correct the three result-affecting specification blockers in OBLIGATION_VALIDITY_PRECISION_MICROBENCH_V1 without broadening the science.
- Re-review the corrected exact design before any implementation.
- If corrected design receives NO_BLOCKING_FINDING, allow exact implementation only; genuine result still requires independent post-result review.
- Keep sealed acceptance benchmark uninspected and acceptance_candidate_frozen=false.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-independent-review-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced evidence as the handoff.
Follow the capsule's next_safe_action.
