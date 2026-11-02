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
- Remote checkpoint: cb6520c5855a7a8b4175411d1eaccff6bde626c5
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

IMMEDIATE POST-OUTAGE V3 ROOT RECOVERY: exact repository correction cb6520c5855a7a8b4175411d1eaccff6bde626c5 passed Workspace Control Validation 41407560030. It proves the prior live updater's metadata contract was wrong: the immutable inactive-install manifest stages the root-activation helper root:root mode 0555, not 0755, and a helper byte refresh also requires its own exact manifest-bound active override attestation. Before any root mutation, terminally cancel temporary diagnostic Lambda validation run 41407093346 through an authority-bearing GitHub surface and re-observe Lambda-side zero assigned/running/transient state; connected GitHub tools cannot cancel that run. Then, from one exact clean checkout at the current validated PR head, execute the corrected transactional scripts/lambda_ci_v3_root_reactivation_helper_live_update_v1.py exactly once as root. The updater must print its prestate proof and refuse any helper digest/owner/group/mode not matching the immutable base manifest. Do not reuse root-reactivation authority receipt /var/lib/workspace-ci/v3/migration/root-reactivation-authority-14e58009-7bf3-43d1-8ad8-7616e70edaa3.json unless consumption state is independently proven; prefer a fresh exact-bound ACTIVATE_V3_ROOT_SERVICES authority if any ambiguity remains. After root services are reactivated and independently attested, resume the frozen migration order at padataset-cpu-public-v1 under its own fresh ACTIVATE_ONE_V3_CANARY authority.

## Remaining work

- Cancel temporary diagnostic Lambda validation run 41407093346 and re-prove Lambda-side legacy assigned/running/transient state is clean; GitHub cancellation alone is not host containment evidence.
- Install the corrected root-reactivation helper exactly once with the transactional validated updater; require exact base manifest helper digest plus root:root mode 0555 prestate and persist the narrow active helper override attestation.
- Independently inspect root-activation authority consumption state; if reuse is not conclusively valid, create a fresh exact-bound ACTIVATE_V3_ROOT_SERVICES authority.
- Reactivate the already-installed v3 reconciler and provisioner transactionally; prove effective installed-generation/controller+helper override attestation, root services healthy, non-target class controllers inactive, no transient/resource claims, and Research GPU containment preserved.
- Complete Workspace Shell reboot hardening from draft PR #592: persist the /run/workspace-shell-control tmpfiles rule and boot-enable only the accepted recovery-plane services with emergency disable preserved.
- Replace repeated operator sudo/bootstrap relay with narrowly reviewed Workspace Shell standing/helper authority for exact GitRunner maintenance/reactivation/canary/cutover operations; never expose generic root shell/systemctl and do not make model reasoning itself an authority source.
- Prepare and execute migration-order #2 padataset-cpu-public-v1 canary under a NEW separately validated one-shot ACTIVATE_ONE_V3_CANARY authority.
- Prepare and execute migration-order #3 padataset-gpu-single-public-v1 canary under its own NEW separately validated one-shot authority.
- After accepted active-class canaries, perform the single production generation cutover: drain/quiesce v2, retarget accepted workflows to exact v3 scale-set names, start only accepted production v3 class controllers, prove exact production serviceability/cleanup, then mark corresponding v2 controllers/scale sets DRAINING -> RETIRED.
- Preserve old installed bytes/config/state for the rollback window and remove legacy v2 config/state only in later cleanup after retirement preconditions hold.
- Keep research-cpu-public-v1 separately gated; keep all Research GPU-derived classes inherited-contained and NO_BY_DEFAULT absent separate containment-recovery authority.
- Keep Research Engine PR #283 draft/proposal-only until separate default-branch producer-cutover authority.

## Blockers / gates

- Power-loss reboot left workspace-ci-v3-reconciler.service and workspace-ci-v3-provisioner.service inactive; direct improvised systemctl activation remains forbidden.
- Temporary diagnostic Lambda validation run 41407093346 is still QUEUED on the legacy lambda-workspace-control lane; because the prior one-shot legacy recovery generation was already consumed, the current v2 controller restart-loops on this new assigned demand. The connected GitHub tool surface exposes no workflow-run cancel mutation, so cancellation is presently an operator-only GitHub action.
- The corrected root-reactivation helper updater is repository-validated but not installed live. Workspace Shell's privileged-helper registry is empty and its reviewed-helper protocol cannot mint operator signatures, so this exact root helper update remains an operator-controlled root execution gate.
- The previously created root-reactivation authority receipt 14e58009-7bf3-43d1-8ad8-7616e70edaa3 has not had its consumption-marker state independently inspected; do not infer replay eligibility.
- Further live v3 migration requires a fresh separately bound one-shot canary authority per class, beginning with padataset-cpu-public-v1.
- Research CPU remains separately gated; Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT; Research Engine PR #283 remains proposal-only.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
