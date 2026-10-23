<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-semantic-control-integration-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-semantic-control-integration-v1
- Title: Semantic Control Integration v1
- Status: BLOCKED_EVIDENCE
- Capsule schema: v2

## Goal

Integrate the validated semantic-control prototype with the real current research-engine and workspace-control authority/data boundaries through read-only, additive adapters and measurable benchmarks, while preserving existing authoritative stores, fail-closed policy semantics, and complete isolation from the still-evolving Local EXTRACT scientific architecture. Measure the missing relational/query baseline, prove cross-system adapter correctness, and bind future accepted EXTRACT outputs only through a versioned adapter before considering any production promotion.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 91459f5f6afa0d71394d63155c2fe8dfdc65a4b7
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 16150517b311b42331ce26978fbb225a760c39e2
- Remote verified: true

## Next safe action

Do not mutate integration or production behavior while BLOCKED_EVIDENCE. On resume, first re-read tasks/active/research-engine-local-extract-redesign-v1.json and its exact referenced research-engine result. Resume bind_accepted_extract_output only if that owning task durably identifies an accepted EXTRACT architecture/output contract with exact artifact/schema identity. Current research-engine@9566532288bf500db8997b9befcc339788609184 ALIGNMENT_AUGMENT_FEASIBLE is explicitly insufficient: it authorizes a new semantic-generalization design phase, not semantic execution or production promotion. Once the gate is genuinely satisfied, create the versioned EXTRACT adapter, rerun the final cross-system benchmark, and only then issue the production-promotion verdict.

## Remaining work

- Wait for the owning EXTRACT task to produce a durable accepted architecture/output checkpoint with exact artifact/schema identity.
- Bind that accepted output through a versioned semantic adapter without changing EXTRACT internals.
- Rerun the final cross-system integration benchmark including the accepted EXTRACT adapter.
- Issue READY_FOR_PRODUCTION_PROMOTION, REVISE, or REJECT; if READY, create a separate production-promotion task.

## Blockers / gates

- BLOCKED_EVIDENCE: research-engine-local-extract-redesign-v1 has not yet produced a durable accepted architecture/output contract. Latest ALIGNMENT_AUGMENT_FEASIBLE result is accepted scientific evidence but explicitly not production promotion and opens another design phase.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-control-integration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
