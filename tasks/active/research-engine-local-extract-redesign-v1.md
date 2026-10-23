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
- Remote checkpoint: f7608b0a22a5be1edc542ab5fbe97b09eea5cc56
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ec592f877bde55c213dadf3a84aad5dec76197c2
- Remote verified: true

## Next safe action

Create a new inert research-engine trigger PR based on the merged zero-generation diagnostic implementation ec592f877bde55c213dadf3a84aad5dec76197c2, then issue exactly one `/local-extract-post-wave7a3-coverage <exact-trigger-head-sha>` comment. Observe that single run to completion, evaluate only the frozen COMPOSITION_CONFIRMED/PARTIAL/NEGATIVE contract, checkpoint its artifact hashes and disposition immediately, and close the trigger PR unmerged. Do not alter selector weights/gates after seeing results, train/download a contribution classifier, start Wave 7B, change production EXTRACT/VERIFY, or introduce ontology/semantic-control mechanisms.

## Remaining work

- Create one inert research-engine trigger PR from implementation checkpoint ec592f877bde55c213dadf3a84aad5dec76197c2 without changing diagnostic semantics.
- Issue exactly one /local-extract-post-wave7a3-coverage <exact-trigger-head-sha> comment and do not issue a second trigger while that run exists.
- Evaluate only COMPOSITION_CONFIRMED/PARTIAL/NEGATIVE from the frozen report, preserve all diagnostic artifacts/hashes, and checkpoint the scientific result immediately.
- Close the inert trigger PR unmerged after result checkpointing.
- Only if COMPOSITION_CONFIRMED may a separate evidence-first contract open compact contribution/discourse classifier training/domain-transfer evaluation.
- Do not start Wave 7B, change production STANDARD Codex EXTRACT or accepted Qwen VERIFY, or introduce ontology/semantic-control mechanisms.

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
