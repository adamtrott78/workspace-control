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

FIRST finish the current legacy workspace-control lane incident diagnosis using the now-live Workspace Shell observability surface from PR #591. Workspace Shell v1 acceptance is complete and the observability updater at PR #591 head 1ca44e019fed66a55f2b9985d9d04397ba37b668 passed live. In a fresh ChatGPT conversation, use the new unit_logs_redacted and maintenance_receipt operations to read the legacy workspace-control controller/maintenance evidence for queued run 41378944347 and maintenance comments 6567987093 / 6567995530. Record exact root cause and bounded repair/serviceability proof. Do NOT repeat the already accepted workspace-control-control-small-v1 canary. After the legacy lane is understood/contained and route serviceability is proven, resume migration-order #2 padataset-cpu-public-v1 under a NEW separately validated one-shot ACTIVATE_ONE_V3_CANARY authority, then PADataset GPU. Preserve all Research GPU-derived NO_BY_DEFAULT containment.

## Remaining work

- Fresh-chat incident diagnosis: use Workspace Shell unit_logs_redacted for workspace-ci-controller@workspace-control-cpu.service and workspace-ci-maintenance-controller.service, plus maintenance_receipt for comments 6567987093 and 6567995530.
- Explain why legacy workspace-control controller is ACTIVE/RUNNING while Lambda validation run 41378944347 remains QUEUED with no runner assignment; distinguish controller liveness, GitHub scale-set/session state, stale job attestation, and maintenance-plane behavior.
- Contain/cancel stale run 41378944347 through the correct scheduler/control-plane mechanism and prove Lambda-side runner/JIT/reservation/process cleanup separately; GitHub scheduler state alone is not host containment evidence.
- Add/verify migration acceptance coverage that a restored legacy route is actually serviceable after v3 canary rollback, not merely that systemd units are active.
- Do not repeat the accepted workspace-control-control-small-v1 first canary.
- After incident/serviceability proof, prepare migration-order #2 padataset-cpu-public-v1 under a new separately validated one-shot ACTIVATE_ONE_V3_CANARY authority. Do not reuse consumed workspace-control authority/transaction.
- Execute padataset-cpu-public-v1 only after exact repository validation and live preflight prove v2/v3 transients drained, v3 root services healthy, and every non-target v3 class inactive.
- After PADataset CPU acceptance, prepare migration-order #3 padataset-gpu-single-public-v1 with the same generation-exclusion/rollback discipline.
- Keep research-cpu-public-v1 inactive unless separately authorized; keep all Research GPU-derived classes NO_BY_DEFAULT until separate containment-recovery authority.
- Keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority.
- Use Workspace Shell as the preferred bounded troubleshooting/terminal transport; widen only by reviewed exact diagnostic/helper capabilities when a concrete operation requires it, never by generic root shell.

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
