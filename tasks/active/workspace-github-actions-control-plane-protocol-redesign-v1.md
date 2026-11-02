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
- Remote checkpoint: f0653307902b324692f8524a843bed55f30428c2
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

PADataset CPU v3 canary is ACCEPTED. Advance to the next separately authorized class only: `padataset-gpu-single-public-v1`. Stage the exact migration-only owner workflow in PADataset from the already-accepted controller/canary generation (controller source 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa; canary generation 7d704ecb6d67ed4dc9421f3675c8facde5c0ffb71f5fd6ba3ab8dc50fc8cafd8), validate its exact blob/route/class binding, and open a draft PADataset PR. Do not dispatch GPU or create live authority until the workflow is on the trusted default branch and a fresh ACTIVATE_ONE_V3_CANARY authority is minted. Do not repeat workspace-control or PADataset CPU canaries.

## Remaining work

- Stage `.github/workflows/workspace-ci-v3-migration-canary-padataset-gpu-single-public-v1.yml` in PADataset from the accepted canary generator/class projection and open a draft PR; record exact blob SHA and expected scale set `lambda-padataset-gpu-single-public`.
- After explicit/default-branch gate is satisfied, execute one bounded `padataset-gpu-single-public-v1` live canary with a fresh ACTIVATE_ONE_V3_CANARY authority and terminal rollback.
- Independently attest roots, v3 class inactivity, exact v2 restoration, PADataset CPU/GPU legacy health as applicable, zero v3 residue, and Research GPU containment.
- Then execute the controlled production v3 cutover and v2 drain/retirement state machine; do not big-bang delete v2.
- Resume `workspace-semantic-execution-migration-v1` after v3 cutover/v2 retirement.

## Blockers / gates

- PADataset GPU canary workflow is not yet trusted on PADataset main; default-branch placement remains a gate before any live GPU authority/dispatch.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.
- Production v3 cutover/v2 retirement remains gated on accepted PADataset GPU canary plus subsequent exact post-canary validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
