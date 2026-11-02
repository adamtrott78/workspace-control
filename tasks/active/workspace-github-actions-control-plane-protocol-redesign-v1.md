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
- Remote checkpoint: ff56679982bc290842a95436ae24adfd568e8c56
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

OPERATOR-ONLY CONTAINMENT REPAIR + V3 ROOT RESUME: the previous post-outage root transaction correctly installed the refreshed helper but root activation failed before authority consumption because legacy workspace-ci-controller@research-engine-gpu.service had rebooted active/running and enabled. Observation-only maintenance diagnose 6571931973 proves service_active=true, UnitFileState=enabled, active_project_units=[], quarantine active_count=0/pending_count=0, reset_pending=[], recovery_state_conflict=false. v3 reconciler/provisioner remain inactive/dead. Exact bounded recovery script scripts/lambda_ci_v3_repair_research_gpu_and_resume_roots_v1.py at head ff56679982bc290842a95436ae24adfd568e8c56 passed Workspace Control Validation 41409276446 SUCCESS. From one exact clean checkout of that validated head, run the script once as root with --expected-head set to that head. It may only stop+disable the exact legacy Research GPU controller after proving no Research execution units and v3 roots inactive, persists a containment receipt, mints a NEW ACTIVATE_V3_ROOT_SERVICES authority, invokes the installed activator, then re-attests Research GPU inactive+disabled and both v3 root services active/running. It never starts/enables Research GPU, touches Research CPU/PADataset/workspace-control v2, activates a v3 class controller, mutates workflows/routes/scale sets, or reuses the failed authority. After it returns, independently verify live state via Workspace Shell and continue padataset-cpu-public-v1 under its own fresh ACTIVATE_ONE_V3_CANARY authority.

## Remaining work

- Execute scripts/lambda_ci_v3_repair_research_gpu_and_resume_roots_v1.py once as root from an exact clean checkout of validated head ff56679982bc290842a95436ae24adfd568e8c56. This repairs only the exact legacy Research GPU controller containment, creates a fresh root authority, and invokes the installed v3 root activator.
- After the wrapper returns, independently attest legacy Research GPU inactive+disabled, v3 reconciler/provisioner active/running, effective installed controller+helper override generation valid, all v3 class controllers inactive, no transient/resource claims, and no Research execution units.
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

- Legacy workspace-ci-controller@research-engine-gpu.service rebooted active/running and enabled, violating inherited Research GPU NO_BY_DEFAULT containment. Diagnose receipt 6571931973 proves no active Research execution units and no active/pending runner units, so exact controller containment repair is safe but still requires operator root execution.
- The validated bounded containment-repair/root-resume script at ff56679982bc290842a95436ae24adfd568e8c56 / run 41409276446 has not yet executed live. Workspace Shell's privileged-helper registry remains empty, so this one root transaction is operator-only.
- Further live v3 migration requires a fresh separately bound one-shot canary authority per class, beginning with padataset-cpu-public-v1.
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
