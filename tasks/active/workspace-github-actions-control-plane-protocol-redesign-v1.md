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
- Remote checkpoint: 6456847b0b4b1268ed6f5bd4d0b847ebde1a21e5
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

P0 INFRASTRUCTURE PRIORITY: complete the v3 active-fleet migration and retire the legacy v2 control plane. First resolve only the minimum legacy workspace-control quarantine/stale-assignment state needed to drain the old scale set safely; do not invest in broad v2 rehabilitation. Then execute the remaining accepted-class canaries in frozen order (padataset-cpu-public-v1, then padataset-gpu-single-public-v1; research-cpu-public-v1 only under separate authority; Research GPU-derived classes remain NO_BY_DEFAULT). After all active-class canaries pass, perform the single production generation cutover defined by architecture/lambda-ci-v3-migration-plan.v1.json: quiesce/drain v2, retarget accepted workflows to v3 scale-set names, start accepted v3 controllers, run exact production validations, prove zero assigned/running jobs and clean ledgers, then mark legacy controllers/scale sets DRAINING -> RETIRED. Preserve rollback bytes/state for the defined rollback window; remove legacy config/state only in later cleanup.

## Remaining work

- Resolve only the current legacy workspace-control assignment-divergence quarantine/stale assigned job sufficiently to reach a safe drain state; do not broaden v2 repair work.
- Contain/cancel stale run 41378944347 through the correct scheduler/control-plane mechanism and separately prove legacy Lambda-side runner/JIT/reservation/process cleanup and old scale-set assigned/running counts zero.
- Prepare and execute migration-order #2 padataset-cpu-public-v1 canary under a NEW separately validated one-shot ACTIVATE_ONE_V3_CANARY authority.
- Prepare and execute migration-order #3 padataset-gpu-single-public-v1 canary under its own NEW separately validated one-shot authority.
- Keep research-cpu-public-v1 inactive unless separately authorized; keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority.
- After all active-class canaries pass, execute the single active-fleet production generation cutover: stop/drain v2, retarget accepted workflows to exact v3 scale-set names, enable/start accepted v3 classes, validate production serviceability, and prove clean ledgers/resources.
- Only after accepted v3 production proof, mark corresponding legacy controllers/scale sets DRAINING then RETIRED and preserve old installed bytes/config/state for the rollback window.
- Delete/retire legacy scale sets only after their per-scale-set preconditions hold; remove legacy controller config/state only in a later cleanup task.
- Keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.
- Use Workspace Shell as the preferred bounded troubleshooting/terminal transport; widen only by reviewed exact diagnostic/helper capabilities when concretely required.

## Blockers / gates

- Current incident gate: legacy workspace-control route has a queued job 41378944347 with no runner assignment even though workspace-ci-controller@workspace-control-cpu.service is ACTIVE/RUNNING. Exact journal/maintenance-receipt evidence requires a fresh ChatGPT conversation because the current chat cached the pre-update MCP schema.
- Run 41378944347 became stale after PR #590 advanced; do not use it as a clean serviceability probe once controller recovery occurs. A correct exact-head attestor may reject it.
- Further live v3 migration still requires a new separately bound one-shot canary authority per class, beginning with padataset-cpu-public-v1.
- Research CPU activation remains separately gated.
- All Research GPU-derived runner classes remain inherited-contained and NO_BY_DEFAULT.
- Research Engine PR #283 remains draft/proposal-only; no default-branch producer cutover is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
