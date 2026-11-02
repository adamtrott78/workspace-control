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
- Remote checkpoint: 675f8772e081052289641211691caeebe6b9f76a
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

OPERATOR-ONLY POST-OUTAGE ROOT RECOVERY TRANSACTION: diagnostic run 41407093346 is cancelled and host cleanup is proven by maintenance diagnose receipt 6571796799 (active_project_units=[], reset_pending=[], recovery_state_conflict=false, active_count=0, pending_count=0; controller logs total_assigned_jobs=0/reconstructable_jobs=0). Exact bounded recovery wrapper scripts/lambda_ci_v3_post_outage_root_recovery_v1.py at head 675f8772e081052289641211691caeebe6b9f76a passed Workspace Control Validation 41408493173. Workspace Shell cannot invoke this root bootstrap because its live helper registry is empty and reviewed-helper approval requires an external operator signature. From one exact clean checkout of the current validated branch head, run the wrapper once as root with --expected-head set to that exact checkout. The wrapper transactionally installs the corrected manifest-bound mode-0555 activation helper, mints a NEW exact installed-manifest/root-policy-bound ACTIVATE_V3_ROOT_SERVICES authority (10-minute lifetime), and invokes only the installed root activation helper. It never reuses authority 14e58009-7bf3-43d1-8ad8-7616e70edaa3, never enables services, never activates a class controller, and never mutates workflows/routes/scale sets/v2 state/Research GPU containment. After it returns, independently attest v3 reconciler/provisioner, effective controller+helper override generation, non-target class inactivity, zero transient/resource claims, and Research GPU containment through Workspace Shell; then resume padataset-cpu-public-v1 under its own fresh ACTIVATE_ONE_V3_CANARY authority.

## Remaining work

- Execute scripts/lambda_ci_v3_post_outage_root_recovery_v1.py once as root from an exact clean validated checkout. This combines only the corrected transactional helper update, fresh ACTIVATE_V3_ROOT_SERVICES authority creation, and installed root activation helper invocation.
- After the wrapper returns, independently attest effective installed generation/controller+helper override, v3 reconciler/provisioner health, all non-target v3 class controllers inactive, no transient/resource claims, and Research GPU containment preserved.
- Complete Workspace Shell reboot hardening from draft PR #592 and establish narrow standing/reviewed helper authority so future exact GitRunner root operations do not require operator sudo relay.
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
- The exact bounded post-outage root recovery wrapper is repository-validated at 675f8772e081052289641211691caeebe6b9f76a / run 41408493173 but has not been executed live. Workspace Shell's helper registry is empty and its privileged protocol requires an external operator signature, so this single root transaction remains operator-only.
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
