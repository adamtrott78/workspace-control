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
- Remote checkpoint: c49c3374a1bcdaabbf013cbc92c92d80705928b4
- Remote verified: true
- Mutation scope: only this task's JSON capsule and Markdown handoff

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: eb492ee8284fc9198bb8d931e3591c870b34ea12
- Remote verified: true
- Mutation scope: none

## Ownership boundary

The EXTRACT chat remains the sole owner of hypotheses, architecture selection, prompts, retrieval/generation, model choices, benchmarks, experiment execution, acceptance criteria, and scientific verdicts.

This review task may independently inspect exact durable evidence, identify methodological or contract problems, and assess downstream bindability. It may not alter EXTRACT or convert reviewer approval into scientific acceptance.

Semantic-control integration remains BLOCKED_EVIDENCE until the EXTRACT owner itself durably identifies a genuinely accepted output contract.

## Review protocol

For each meaningful EXTRACT checkpoint:

1. Re-read the authoritative EXTRACT capsule.
2. Resolve the exact referenced research-engine SHA, result/report, artifact hashes, frozen gate, and relevant controls.
3. Check methodological consistency, control parity, evidence completeness, and whether the claimed disposition follows from the predeclared gate.
4. Check downstream compatibility only against the opaque consumer-side socket. Do not require RDF, ontology-native output, SemanticObservationV1, or semantic-control-specific schema upstream.
5. Persist only material findings in this task capsule as an independent review checkpoint.
6. The EXTRACT owner decides whether and how a review finding changes its own next action.
7. If an accepted EXTRACT output contract eventually appears, perform a bindability audit and hand exact evidence to workspace-semantic-control-integration-v1; do not implement the adapter here.

## Current baseline

- HARDENING_PASS: research-engine@33b44e201b8464dd033b748afe34a5f7e26646cd
- PRE_EXTRACT_INTEGRATION_PASS: research-engine@16150517b311b42331ce26978fbb225a760c39e2
- Latest EXTRACT checkpoint: research-engine@eb492ee8284fc9198bb8d931e3591c870b34ea12
- Latest EXTRACT verdict: NLI_CERTIFICATE_REJECTED
- Accepted lexical preservation evidence remains ALIGNMENT_AUGMENT_FEASIBLE; it is not an accepted output contract.

## Next safe action

Validate and merge this task-only review contract. Then re-read the latest EXTRACT capsule before the first substantive review; review only exact durable checkpoints and publish findings here without mutating EXTRACT or integration.

## Fresh-chat initialization

@GitHub
@Heartbeat

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-independent-review-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced EXTRACT/integration evidence as the complete handoff.
Do not rely on previous conversation state.
Use Workspace Heartbeat with the same real task ID when actively reviewing.
Follow the capsule's next_safe_action.
