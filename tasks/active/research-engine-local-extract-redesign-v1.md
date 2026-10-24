<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: CHECKPOINTED
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
- Remote checkpoint: c6ccffc1b060495f2c54cf74b15b193535c32f5a
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 329e7e5a31553551e39d4384a09f2c406c4a3e2f
- Remote verified: true

## Next safe action

Checkpoint the validated AMR implementation, then add only the smallest declarative workspace-control route binding for workload model-eval-local-extract-amr-graph-v1 to the existing gpu-single-public-ci-v1 contract and trusted workflow blob 70483ed29dffc19ec8e3c8eaa754321e6f44b653. Reconcile trusted state before exactly one external-only validation trigger. Do not redesign runner/controller/provisioner infrastructure and do not access EXTRACT teacher inputs.

## Remaining work

- Bind the AMR validation workflow/command declaratively to the existing lambda-research-engine-gpu gpu-single-public-ci-v1 execution contract; do not redesign GitRunner/controller/provisioner/runtime infrastructure.
- Trusted-reconcile the route/workflow identity before any AMR parser execution.
- After durable route readiness, create an inert exact-SHA trigger PR and issue exactly one AMR_GRAPH_REDUNDANCY_CERTIFICATE_VALIDATION_V1 trigger.
- Evaluate only frozen AMR_GRAPH_CERTIFICATE_VALIDATED/PARTIAL/REJECTED and persist exact run/artifact/report/parser/tokenizer/data identities.
- At the result checkpoint, re-read workspace-local-extract-independent-review-v1 before selecting another scientific phase.
- Do not use EXTRACT teacher labels, alter production EXTRACT/VERIFY, start Wave 7B, train/fine-tune the parser, or emit semantic-control/RDF/ontology output.

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
