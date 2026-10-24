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
- Remote checkpoint: 5b0107ead0a559a25dc72c9b452eb46b485d7397
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 02e12643e64756395f09cafca1b36cae80dbb085
- Remote verified: true

## Next safe action

At durable AMR design checkpoint research-engine@02e12643e64756395f09cafca1b36cae80dbb085, re-read tasks/active/workspace-local-extract-independent-review-v1.json and consume any review explicitly tied to this exact design SHA. If none exists, proceed without waiting: implement only the external AMR_GRAPH_REDUNDANCY_CERTIFICATE_VALIDATION_V1 from isolated design head 50cf3ae923552712fd6f2159d1ef0afa064dbd43, with no EXTRACT teacher input or EXTRACT AMR experiment.

## Remaining work

- Re-read workspace-local-extract-independent-review-v1 at exact AMR design SHA research-engine@02e12643e64756395f09cafca1b36cae80dbb085; consume only an exact applicable review if present, otherwise proceed without waiting.
- Implement only external AMR_GRAPH_REDUNDANCY_CERTIFICATE_VALIDATION_V1 from isolated design head 50cf3ae923552712fd6f2159d1ef0afa064dbd43.
- Verify parser model asset size/MD5, compute and record parser tarball SHA256, pin Bio-AMR mirror bytes and SPARK blob, and enforce deterministic Smatch internal reseeds.
- Run normal CI and durable-checkpoint implementation before exactly one external AMR validation trigger.
- Evaluate only AMR_GRAPH_CERTIFICATE_VALIDATED/PARTIAL/REJECTED from frozen SPARK and Bio-AMR gates.
- Do not use EXTRACT teacher labels, retune prior lexical/NLI/predicate-argument gates, train/fine-tune AMR, start Wave 7B, alter production EXTRACT/VERIFY, or emit semantic-control/RDF/ontology payloads.

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
