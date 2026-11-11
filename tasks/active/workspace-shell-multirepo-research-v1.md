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
- Remote checkpoint: 50395aad06ab719b8207d9e7d3d8270a6bb35030
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 4c095352bfe128e93f794112741efdb7a66b9c38
- Remote verified: true

## Next safe action

Rebuild/port the workspace-control multirepo candidate onto the accepted V3 controller lineage while preserving the PR #595 task delta, validate the new exact candidate head through the current V3 workflow, then refresh Workspace Shell authority/runtime only after that new exact head passes.

## Remaining work

- Create a new exact workspace-control candidate that contains the PR #595 multirepo changes plus the accepted V3 controller source/provenance lineage; do not treat failed 50395aad as valid.
- Prepare and independently review a bounded live v3 production-controller refresh/revival transaction; do not touch retired v2 workspace-control controller generation.
- Repair/revive only the exact #389 REST terminal record under reviewed semantics and allow run #389 to validate candidate 50395aad06ab719b8207d9e7d3d8270a6bb35030.
- After exact-head validation passes, refresh Workspace Shell authority/runtime to workspace-control 50395aad06ab719b8207d9e7d3d8270a6bb35030 and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38.
- Verify both live durable task gates, then resume MTH602 Stage 03 deterministic tests and architecture-C evaluation.

## Blockers / gates

- V3 runtime repair is closed: run #389 received the correct fresh runner and executed. The remaining blocker is that PR #595 candidate 50395aad predates the V3 controller subtree required by the current validation workflow.
- Live transaction semantics are approved, but Workspace Shell cannot execute them without a pre-admitted helper registry entry and externally signed off-Lambda workspace-shell-approval.v1; the connected ChatGPT surface cannot mint this authority.
- Even after code review acceptance, no live v3 controller deployment or ledger revival is authorized until a separate source-bound live refresh transaction is designed, validated, and independently reviewed.
- PADataset Stage 03 remains blocked until workspace-control exact-head validation completes and the parent runtime refresh can safely bind Workspace Shell to PADataset candidate 4c095352bfe128e93f794112741efdb7a66b9c38.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
