<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 242feb1cc3be798f656a5ece97b15f60264ce7dd
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 12d8ad19d14f2ab42474e159f958060f3050cf1e
- Remote verified: true

## Next safe action

PADataset CPU v3 canary is accepted and durably validated. GPU canary workflow is staged as draft PADataset PR #4 at exact head 0b7a1884c4a60046ce220f04f20b5e4ecdb598eb with exact blob 9311657f079aa1894d16d5e83ed0b18a813af487. Next action is the explicit/default-branch trust gate: merge PR #4 into PADataset main only with user authorization. After merge, independently verify the exact workflow blob on main, then create a fresh one-shot ACTIVATE_ONE_V3_CANARY authority and execute exactly `padataset-gpu-single-public-v1`. Do not repeat workspace-control or PADataset CPU canaries.

## Remaining work

- Obtain explicit user authorization to merge PADataset draft PR #4.
- After merge, verify PADataset main contains exact GPU canary workflow blob 9311657f079aa1894d16d5e83ed0b18a813af487 and resolve the resulting workflow ID.
- Execute one bounded `padataset-gpu-single-public-v1` canary with a fresh ACTIVATE_ONE_V3_CANARY authority, then terminal rollback.
- Independently attest roots, all v3 class inactivity as permitted, zero v3 resource/transient residue, exact v2 restoration, PADataset lane health, and Research GPU containment; record GPU acceptance.
- Then execute controlled production v3 cutover/v2 retirement and resume `workspace-semantic-execution-migration-v1`.

## Blockers / gates

- PADataset GPU canary workflow is staged only in draft PR #4 and is not yet trusted on PADataset main; merge/default-branch placement is an explicit user gate.
- No GPU live authority may be created and no GPU workflow may be dispatched before exact default-branch blob verification.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.
- Production v3 cutover/v2 retirement remains gated on accepted PADataset GPU canary plus exact post-canary validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
