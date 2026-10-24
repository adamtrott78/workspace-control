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
- Remote checkpoint: 2b4a6ab43114107a9c5b1d5ff96272abc236fe34
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8f03b818f415b33c3a3d0bd92d2c7396920013d6
- Remote verified: true

## Next safe action

Do not issue another `/lambda-ci-local-extract-amr-graph-certificate-validation` V1 trigger. Treat the single authorized trigger as consumed by run 40062934298, which failed before scientific execution, so the AMR scientific certificate is NOT_RUN. Before any future AMR external execution, first establish a new explicit predeclared execution-authority checkpoint with a fresh inert exact-SHA anchor derived from repaired research-engine@8f03b818f415b33c3a3d0bd92d2c7396920013d6, re-read workspace-local-extract-independent-review-v1, and preserve the frozen scientific identities/gates unless newer durable design authority explicitly changes them.

## Remaining work

- AMR graph scientific certificate remains NOT_RUN; do not issue another V1 trigger.
- If AMR external validation is resumed, first create and durably validate a new explicit one-shot execution-authority checkpoint with a fresh inert exact-SHA anchor based on repaired research-engine state.
- Re-read workspace-local-extract-independent-review-v1 at that future checkpoint; current reviewer state has no exact AMR failure/hotfix finding.
- Preserve all frozen AMR parser/model/tokenizer/data/Smatch identities and scientific gates unless newer durable design authority explicitly changes them.
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
