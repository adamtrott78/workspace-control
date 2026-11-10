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
- Remote checkpoint: ce19452c644599bda23f6e3766c9390fa0d906db
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 17e1147614f27702e43565089d618182ff71c5af
- Remote verified: true

## Next safe action

Apply the validated rollback-capable multirepo upgrade from the exact authority-state branch head, with workspace-control execution candidate ce19452c644599bda23f6e3766c9390fa0d906db and PADataset execution SHA 17e1147614f27702e43565089d618182ff71c5af. The upgrade must refresh /etc/workspace-shell/authority separately from /srv/workspace-shell/workspace-control and must report LOCAL_TASK_AUTHORITY=PASS. Immediately afterward, re-test both durable task IDs through the ChatGPT Workspace Shell connector before any PADataset Stage 00 read.

## Remaining work

- Deploy the validated multirepo upgrade using the exact authority-state branch head, workspace-control execution candidate ce19452c644599bda23f6e3766c9390fa0d906db, and PADataset execution SHA 17e1147614f27702e43565089d618182ff71c5af.
- Verify live task visibility for workspace-shell-multirepo-research-v1 and mth602-final-multisurrogate-dqnguard-v1.
- Run positive and negative PADataset Workspace Shell acceptance at exact SHA 17e1147614f27702e43565089d618182ff71c5af.
- Begin MTH602 Stage 00 provenance recovery from the clean execution snapshot plus the untouched read-only historical evidence checkout.
- Wire research-bounded to the real DNNs/CUDA runtime internally without changing the external MCP schema.

## Blockers / gates

- Live trusted task authority is still stale: workspace-shell-multirepo-research-v1 and mth602-final-multisurrogate-dqnguard-v1 return TASK_NOT_FOUND. This is now the sole execution gate before PADataset Stage 00.
- The live authority refresh is a host mutation outside the currently visible task authority. It must be applied through the validated operator upgrade path; do not bypass with workspace-shell-mcp-v1 or touch PADataset first.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
