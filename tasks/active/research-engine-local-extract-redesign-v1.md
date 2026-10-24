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
- Remote checkpoint: 41e5c729ec2eab2cce95aefc138878fad4d265a6
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 329e7e5a31553551e39d4384a09f2c406c4a3e2f
- Remote verified: true

## Next safe action

After this pre-run checkpoint validates and merges, issue exactly one `/lambda-ci-local-extract-amr-graph-certificate-validation 4818bed9d51830406a7521be225ea28f9e3ca323` comment on open research-engine PR #227. Bind the resulting run to that exact SHA and do not issue a second trigger. Evaluate only the frozen AMR graph certificate verdict.

## Remaining work

- Issue exactly one /lambda-ci-local-extract-amr-graph-certificate-validation 4818bed9d51830406a7521be225ea28f9e3ca323 comment on research-engine PR #227.
- Observe only the unique external-only AMR validation run; do not retrigger while it is active.
- Evaluate only frozen AMR_GRAPH_CERTIFICATE_VALIDATED/PARTIAL/REJECTED and persist exact run/artifact/report/parser/tokenizer/data identities.
- Close research-engine PR #227 unmerged after the result is durably checkpointed.
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
