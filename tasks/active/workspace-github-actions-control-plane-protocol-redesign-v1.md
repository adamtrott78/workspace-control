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
- Remote checkpoint: dce2327105a886cca78473dbec355c9e6b3610bc
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

PADataset CPU stale-v3 restart residue has been explicitly extinguished with the hardened rollback helper. The prior transaction receipt b899379d-7e33-4b28-90db-10fbbcc8d24b was replayed through the hardened helper and returned V3_CANARY_ROLLBACK=PASS / STALE_V3_CONTROLLER_RECOVERY=PASS. Independent post-recovery evidence: roots healthy (reconciler active/exited, provisioner active/running), workspace-control v2 CPU active/running, PADataset v2 CPU diagnose 6573255183 PASS active/running with no active project units/reset/recovery conflict, Research GPU diagnose 6573256344 PASS inactive/dead+disabled with no active/pending/reset/recovery conflict. Rollback race hardening is at 2af7c8bba198b5b0e58ede6f8d34d0b64c8ed0af and the operator pins that hardened helper at dce2327105a886cca78473dbec355c9e6b3610bc; Validation 41417808454 SUCCESS. The PADataset operator also retains the explicit target repository fix, so its preflight must attest V3_SCALE_SET_TARGET_URL=https://github.com/adamtrott78/PADataset. Next safe action: one fresh-authority PADataset CPU canary retry from the exact validated durable head after this task-state sync. Retry-history must recognize both prior rolled-back CPU transactions and mint a new authority.

## Remaining work

- Rerun `scripts/lambda_ci_v3_padataset_cpu_canary_live.sh` once from the exact clean validated durable head after task-state sync.
- Require retry-history to report both prior rolled-back target transactions and matched authority markers; require all class preflights inactive with ActiveState/SubState checks and require `V3_SCALE_SET_TARGET_URL=https://github.com/adamtrott78/PADataset` before authority creation.
- Allow the canary to reach terminal completion without manual interruption. The hardened rollback helper must unconditionally stop the target class on every rollback, cancelling any pending Restart=on-failure job.
- After CPU canary success and generation-exclusion rollback, independently attest roots, v3 class inactivity as far as authorized inspection permits, zero v3 residue, exact v2 restoration, and Research GPU containment; then record CPU acceptance.
- Then stage/authorize/execute padataset-gpu-single-public-v1 under its own fresh authority, followed by controlled production v3 cutover/v2 retirement and resumption of the semantic execution umbrella task.

## Blockers / gates

- CPU canary remains unaccepted; all previous live CPU attempts are historical/cancelled or pre-authority failures.
- Every retry must pass retry-history and mint a fresh ACTIVATE_ONE_V3_CANARY authority; no prior authority may be reused.
- Workspace Shell cannot directly inspect the PADataset v3 class unit because it is not in the fixed unit allowlist; the hardened rollback was therefore verified by its exact receipt result plus restored v2 state, and the next operator preflight must independently prove all v3 class units inactive/non-restarting before authority creation.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
