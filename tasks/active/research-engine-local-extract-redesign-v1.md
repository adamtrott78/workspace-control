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
- Remote checkpoint: bd76a3a79aa5e0880aa6659c9518bdc68cbd753d
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5c30b580a8315fc74741aff212f45d09d2afcb81
- Remote verified: true

## Next safe action

Implement only AMR_GRAPH_REDUNDANCY_CERTIFICATE_VALIDATION_V1 from isolated final design head 7749bd2092cf3d1250dcdc8bacf3b31684417c4c using the existing lambda-research-engine-gpu lane. No exact independent-review checkpoint exists for final design SHA 5c30b580a8315fc74741aff212f45d09d2afcb81, so proceed without waiting. No EXTRACT teacher input or EXTRACT AMR experiment is authorized.

## Remaining work

- Implement external AMR_GRAPH_REDUNDANCY_CERTIFICATE_VALIDATION_V1 from isolated final design head 7749bd2092cf3d1250dcdc8bacf3b31684417c4c using existing lambda-research-engine-gpu.
- Pin amrlib@38b29706ea982da5a5b081a04f00c93cc6cc1e9c, parser asset id 57066548/size/MD5/SHA256, facebook/bart-large tokenizer revision 22fa33834dccc11df99c4fc5fcc96c67f806dfdb, Smatch v1.0.4 commit 1bcd49cc8535056aa1c941763580fc5a572f1204, SPARK blob, and Bio-AMR mirror blob.
- Run normal CI and durable-checkpoint implementation before exactly one external AMR validation trigger.
- Evaluate only frozen AMR_GRAPH_CERTIFICATE_VALIDATED/PARTIAL/REJECTED.
- At the eventual result checkpoint, re-read independent-review before selecting another scientific phase.
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
