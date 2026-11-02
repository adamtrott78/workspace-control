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
- Remote checkpoint: 74c027df26253c9836f23240f7456623a5979859
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

IMMEDIATE POST-OUTAGE V3 ROOT REACTIVATION GATE: do not rerun the failed live updater or root activation blindly. Exact repository head 74c027df26253c9836f23240f7456623a5979859 passed Workspace Control Validation run 41405429998 and makes root reactivation aware of the accepted ACTIVE controller-refresh override. The operator then ran scripts/lambda_ci_v3_root_reactivation_helper_live_update_v1.py, which failed CLOSED before mutation with `installed helper metadata mismatch: /opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py`. First recover the exact live helper metadata/digest/ownership/mode and prior activation/update receipts using Workspace Shell/read-only host evidence; compare them to the updater's frozen expected prestate and determine why the installed helper does not match. Correct only the updater/prestate contract if required, validate the exact new head, then perform one transactional helper update. Treat the previously created root-reactivation authority receipt /var/lib/workspace-ci/v3/migration/root-reactivation-authority-14e58009-7bf3-43d1-8ad8-7616e70edaa3.json as non-reusable until its consumption state is independently proven; issue a fresh ACTIVATE_V3_ROOT_SERVICES authority if there is any ambiguity. After reconciler/provisioner are healthy, resume the frozen migration order at padataset-cpu-public-v1 under a fresh class-specific ACTIVATE_ONE_V3_CANARY authority.

## Remaining work

- Resolve the exact installed-helper metadata mismatch blocking the validated refresh-aware root-reactivation helper; do not widen authority or bypass installed-byte/metadata attestation.
- Reactivate the already-installed v3 reconciler and provisioner after the power-loss reboot using fresh installed-manifest-bound ACTIVATE_V3_ROOT_SERVICES authority; prove controller-refresh override attestation, root services healthy, non-target class controllers inactive, and Research GPU containment preserved.
- Complete Workspace Shell reboot hardening from draft PR #592: persist the /run/workspace-shell-control tmpfiles rule and boot-enable only the accepted recovery-plane services with emergency disable preserved.
- Replace repeated operator sudo/bootstrap relay with narrowly reviewed Workspace Shell standing/helper authority for exact GitRunner maintenance/reactivation/canary/cutover operations; never expose generic root shell/systemctl and do not make model reasoning itself an authority source.
- Prepare and execute migration-order #2 padataset-cpu-public-v1 canary under a NEW separately validated one-shot ACTIVATE_ONE_V3_CANARY authority.
- Prepare and execute migration-order #3 padataset-gpu-single-public-v1 canary under its own NEW separately validated one-shot authority.
- After accepted active-class canaries, perform the single production generation cutover: drain/quiesce v2, retarget accepted workflows to v3 scale-set names, start accepted production v3 class controllers, prove exact production serviceability/cleanup, then mark corresponding v2 controllers/scale sets DRAINING -> RETIRED.
- Preserve old installed bytes/config/state for the rollback window and remove legacy v2 config/state only in later cleanup after retirement preconditions hold.
- Keep research-cpu-public-v1 separately gated; keep all Research GPU-derived classes inherited-contained and NO_BY_DEFAULT absent separate containment-recovery authority.
- Keep Research Engine PR #283 draft/proposal-only until separate default-branch producer-cutover authority.

## Blockers / gates

- Power-loss reboot left workspace-ci-v3-reconciler.service and workspace-ci-v3-provisioner.service inactive; migration plan forbids improvised direct systemctl activation.
- Validated refresh-aware root-reactivation candidate 74c027df26253c9836f23240f7456623a5979859 / run 41405429998 SUCCESS is not live: transactional updater failed before mutation on installed helper metadata mismatch for /opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py.
- The previously created root-reactivation authority receipt may have been created before the failed activation/update sequence; consumption/replay eligibility must be proven from durable authority state, never inferred.
- Workspace Shell privileged-helper registry/standing root authority is still insufficient for this root bootstrap class, so the architecture still has an operator-terminal relay gap to eliminate.
- Further live v3 migration requires a fresh separately bound one-shot canary authority per class, beginning with padataset-cpu-public-v1.
- Research CPU activation remains separately gated; Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT; Research Engine PR #283 remains proposal-only.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
