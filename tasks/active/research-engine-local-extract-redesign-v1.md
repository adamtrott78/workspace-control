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

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 444b71c07461dbf1087f8aa446bcb314152e6842
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e7b521311e71e4050565eb63168b63c5d2374a40
- Remote verified: true

## Next safe action

Re-read tasks/active/workspace-local-extract-independent-review-v1.json for any review explicitly tied to research-engine@e7b521311e71e4050565eb63168b63c5d2374a40. If none exists, proceed without waiting: implement only AMR_GRAPH_REDUNDANCY_CERTIFICATE_VALIDATION_V1 from isolated final design head bf0788646d91b9b7d764b7fd739e0b8a4132e9db using the existing lambda-research-engine-gpu lane.

## Remaining work

- Re-read workspace-local-extract-independent-review-v1 for an exact review tied to research-engine@e7b521311e71e4050565eb63168b63c5d2374a40; if none exists, proceed without waiting.
- Implement only external AMR_GRAPH_REDUNDANCY_CERTIFICATE_VALIDATION_V1 from isolated final design head bf0788646d91b9b7d764b7fd739e0b8a4132e9db.
- Use existing lambda-research-engine-gpu lane; do not redesign GitRunner/controller infrastructure.
- Pin amrlib 0.8.1 source commit, parser asset size/MD5/SHA256, facebook/bart-large tokenizer revision 22fa33834dccc11df99c4fc5fcc96c67f806dfdb + manifest SHA256, Smatch v1.0.4 deterministic reseed behavior, SPARK blob, and Bio-AMR mirror blob.
- Run normal CI and durable-checkpoint implementation before exactly one external AMR validation trigger.
- Evaluate only frozen AMR_GRAPH_CERTIFICATE_VALIDATED/PARTIAL/REJECTED; no EXTRACT teacher labels or EXTRACT AMR experiment.

## Blockers / gates

- None.
