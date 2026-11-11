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
- Remote branch: workspace-shell-multirepo-v3-reconcile-20261111
- Remote checkpoint: f7ed7305e904ec24a444f7a488ca07e9bef4fdc7
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: 81ee9bf2a06949ce1e9477befe00f833248d8ea3
- Remote verified: true

## Next safe action

Validate this exact combined authority snapshot. Do not perform the root-owned live refresh until the authority validation passes.

## Remaining work

- Validate this combined state-only authority snapshot.
- After PASS, operator installs workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7 and PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3.
- Verify live exact bindings and rerun tests/test_multisurrogate_dqnguard.py through research-bounded.
- Prepare one known-only four-class backbone target fold with cache_len=16384 and no target-informed checkpoint selection.
- Use a sanctioned PyTorch-capable scientific compute surface for the real Architecture C small run; do not widen Workspace Shell by exposing /home.

## Blockers / gates

- Live Workspace Shell still uses execution ca2241d44d5563b137f4c6978b33dfc060d2a968 and PADataset 4c095352bfe128e93f794112741efdb7a66b9c38; combined validated candidate is workspace-control f7ed7305e904ec24a444f7a488ca07e9bef4fdc7 + PADataset 81ee9bf2a06949ce1e9477befe00f833248d8ea3.
- The next mutation is root-owned and must use the existing rollback-capable operator upgrade after this authority snapshot passes validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
