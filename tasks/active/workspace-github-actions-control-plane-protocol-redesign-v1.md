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
- Remote checkpoint: f8057d2925a329b773b312b62e897e4830e9d54c
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

ROOT RECOVERY COMPLETE; PREPARE PADATASET CPU CANARY. Live authority cbada5b8-4a9d-4a61-bae2-1cfc621a0960 completed V3_ROOT_SERVICES_ACTIVATION=PASS. Independent Workspace Shell evidence after activation: workspace-ci-v3-reconciler.service ActiveState=active/SubState=exited with V3_INSTALLED_GENERATION_VERIFY=PASS (healthy Type=oneshot/RemainAfterExit semantics); workspace-ci-v3-provisioner.service active/running; workspace-control-control-small-v1 class controller inactive/dead. Fresh post-activation Research GPU diagnose receipt 6572239135 proves legacy research-engine GPU controller inactive/dead + disabled, active_project_units=[], active_count=0, pending_count=0, reset_pending=[], recovery_state_conflict=false. The wrapper's final ERROR was a false-negative health predicate that incorrectly required the reconciler oneshot to be running; exact fix f8057d2925a329b773b312b62e897e4830e9d54c passed Workspace Control Validation 41411117818 SUCCESS and also invokes the verifier updater with python -B to prevent sudo-owned repository __pycache__ cleanup residue. Do NOT rerun root activation. Next: prepare padataset-cpu-public-v1 canary against accepted controller source head 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa, preserving separate fresh ACTIVATE_ONE_V3_CANARY authority and requiring the exact generated owner-only migration workflow blob on PADataset main before any live canary transaction.

## Remaining work

- Stage/review the exact generated PADataset CPU migration canary workflow `.github/workflows/workspace-ci-v3-migration-canary-padataset-cpu-public-v1.yml` in adamtrott78/PADataset; generated blob must bind the accepted controller/canary source generation.
- Prepare and validate a padataset-cpu-public-v1 live operator using accepted controller source head 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa, exact canary workflow blob, repository-scoped PADataset credential group, and the existing generation-exclusion transaction/rollback protocol.
- Only after the exact workflow is on PADataset main and the operator preflights cleanly, consume one fresh ACTIVATE_ONE_V3_CANARY authority, run the CPU canary, rollback generation exclusion to exact v2 prestate, and independently attest root/class/resource/Research-GPU state.
- Then repeat the same separately-authorized process for padataset-gpu-single-public-v1.
- After PADataset CPU+GPU canaries are accepted, perform controlled production v3 cutover and v2 retirement; then resume workspace-semantic-execution-migration-v1 umbrella work.

## Blockers / gates

- PADataset CPU canary workflow is not currently present on adamtrott78/PADataset main; the exact owner-only migration workflow must be staged/reviewed and land on the owning default branch before live dispatch.
- Live padataset-cpu-public-v1 still requires its own fresh exact-bound ACTIVATE_ONE_V3_CANARY authority; no authority from root activation or the accepted workspace-control canary may be reused.
- Research CPU remains separately gated; all Research GPU-derived v3 classes remain inherited-contained and NO_BY_DEFAULT; Research Engine PR #283 remains proposal-only.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
