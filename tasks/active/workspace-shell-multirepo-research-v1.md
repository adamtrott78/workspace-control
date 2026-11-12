<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Extend the live Workspace Shell v1 lineage with a first-class PADataset target that supports exact-SHA/task-bound Git provenance, bounded read-only evidence inspection, and sandboxed network-denied research execution without exposing a generic shell or making the historical PADataset checkout writable.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-multirepo-research-v1
- Remote checkpoint: 1a9a24fc1bc6e5cda2984e296151a378138600c8
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 17e1147614f27702e43565089d618182ff71c5af
- Remote verified: true

## Next safe action

Rerun the validated rollback-capable multirepo upgrade from the exact authority-state branch head produced by this checkpoint, with workspace-control execution candidate 1a9a24fc1bc6e5cda2984e296151a378138600c8 and PADataset execution SHA 17e1147614f27702e43565089d618182ff71c5af. The upgrader must verify/reuse the existing PADataset evidence mount safely, refresh /etc/workspace-shell/authority separately, and report LOCAL_TASK_AUTHORITY=PASS. Then re-test both durable task IDs through ChatGPT Workspace Shell before any Stage 00 read.

## Remaining work

- Deploy the validated multirepo upgrade using the final authority-state head, workspace-control execution candidate 1a9a24fc1bc6e5cda2984e296151a378138600c8, and PADataset execution SHA 17e1147614f27702e43565089d618182ff71c5af.
- Verify live task visibility for workspace-shell-multirepo-research-v1 and mth602-final-multisurrogate-dqnguard-v1.
- Run positive and negative PADataset Workspace Shell acceptance at exact SHA 17e1147614f27702e43565089d618182ff71c5af.
- Begin MTH602 Stage 00 provenance recovery from the clean execution snapshot plus the untouched read-only historical evidence checkout.
- Wire research-bounded to the real DNNs/CUDA runtime internally without changing the external MCP schema.

## Blockers / gates

- Live trusted task authority is still stale: workspace-shell-multirepo-research-v1 and mth602-final-multisurrogate-dqnguard-v1 return TASK_NOT_FOUND. This remains the sole execution gate before PADataset Stage 00.
- The validated host upgrade must be rerun from the new authority-state head with workspace-control execution candidate 1a9a24fc1bc6e5cda2984e296151a378138600c8. The existing evidence mount may now be reused only if the upgrader verifies its identity and read-only hardening.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
