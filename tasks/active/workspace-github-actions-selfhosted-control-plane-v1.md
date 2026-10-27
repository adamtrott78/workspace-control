<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-selfhosted-control-plane-v1
- Title: GitHub Actions Self-Hosted Control Plane v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: revise_control_plane_design_v0_2

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, per-project isolation, fail-closed admission, review gates, and a clean path to GitHub organization runner groups. Also reduce operator copy/paste by making review targets and dispositions durable and GitHub-native.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-selfhosted-control-plane-v1
- Remote checkpoint: c69f6632c6274312f6fb0449d9f4d7789319fd7c
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Independent review disposition

- Exact architecture: `architecture/github-actions-selfhosted-control-plane.v0.1.json@f70f100ba57140469ff656255de00f7de262dbc3`
- Exact manifest: `architecture/lambda-ci-project-workspace-control.v1.json@efa6e09f4206ca1d1d2fe6daaabcb69ed01d4588`
- Required runtime evidence consumed: PR #508 comments `6405597751` and `6408089808`
- PR head reviewed: `c69f6632c6274312f6fb0449d9f4d7789319fd7c`
- Mechanical validation: run `40423934526` SUCCESS
- GitHub review: `5661002925`
- Disposition: **BLOCKING FINDINGS**
- P1 live activation: **NOT AUTHORIZED**

### BF-1 — stale-assignment recovery

Frozen v0.1 does not define authoritative recovery when GitHub reports assigned-job state but the restarted controller lacks complete authoritative per-job recovery metadata. With `maxRunners=1`, that can indefinitely wedge the lane. v0.2 must freeze fail-closed divergence detection, quarantine/no-new-acquisition, bounded cleanup/reset, proof of zero live/stale assignments before one replacement trigger, duplicate-trigger suppression, durable receipts, and recovery tests. Do not solve this by merely increasing `maxRunners`.

### BF-2 — privileged maintenance/recovery authority

Frozen v0.1 does not define the bounded owner-restricted authority needed for controller restart, exact reviewed profile/policy installation, reconciliation activation, stale cleanup, and bounded diagnostics. v0.2 must freeze an allowlisted command/target surface with exact trusted identity/blob checks, independent root-side validation, receipts/rollback, no arbitrary shell/path/systemd-property authority, no untrusted/fork invocation, and no circular dependence on L1 as its own sole repair authority.

### Explicit non-blockers

Bootstrap non-circularity and the NOT_INSTALLED isolation scaffold are acceptable. P1 may remain host-wide serialized with `concurrency=1` / `maxRunners=1` temporarily; global serialization is an efficiency/liveness limitation, not a pre-P1 safety blocker. Any capacity increase still requires separately reviewed resource-aware arbitration. Transport identity remains routing-only; root execution contracts/profiles remain resource authority. GitHub organization migration remains separately gated P3 work.

## Next safe action

Revise and freeze a bounded v0.2 control-plane design before any P1 activation. v0.2 must address BF-1 authoritative stale-assignment recovery (fail-closed divergence detection, lane quarantine, bounded cleanup/reset, zero-live/stale proof before retrigger, duplicate-trigger suppression, receipts/tests) and BF-2 bounded owner-restricted privileged maintenance/recovery authority (allowlisted verbs/targets, exact trusted identity/blob checks, root-side validation, no arbitrary root command surface, non-circular recovery, receipts/rollback). Keep P1 serialized at concurrency=1/maxRunners=1 temporarily; do not increase capacity until resource-aware host arbitration is separately reviewed. Preserve independent L0 bootstrap, workspace-control isolation, transport-versus-execution authority separation, P3 organization deferral, and existing rollback paths. Freeze exact v0.2 architecture/manifest blobs and obtain a fresh independent review before implementation. Do not activate a live workspace-control runner and do not continue EXTRACT science in this task.

## Remaining work

- Revise and freeze a bounded v0.2 control-plane design addressing BF-1 stale-assignment recovery and BF-2 privileged maintenance/recovery authority without widening scientific or execution authority.
- Make v0.2 explicitly preserve P1 host-wide serialization/concurrency=1 as a temporary safe constraint; do not raise maxRunners until separately reviewed resource-aware host arbitration exists.
- Freeze exact v0.2 architecture and workspace-control manifest blobs, then obtain a fresh independent preimplementation review.
- Only after v0.2 receives NO_BLOCKING_FINDING, implement and validate the P1 owner-commanded workspace-control JIT pilot while leaving bootstrap reconciliation authority independent.
- Design/review resource-aware host arbitration before any runner-count/concurrency increase; preserve explicit CPU/RAM/GPU envelopes and fail-closed admission.
- Design/review control-small and automatic pull_request/push admission as P2.
- Migrate routine hosted CI only after the pilot and automatic-event gates pass.
- Evaluate and separately execute GitHub organization migration with configurable runner-group IDs, organization-scoped GitHub configuration, owner/repository attestation migration, and least-privilege GitHub App credentials.
- Automate routine review request/consumption so the operator does not ferry text between chats while preserving reviewer independence.
- Retire the temporary public workspace-control and GPU-listener transport workarounds only after reviewed replacement paths are live and rollback-safe.

## Blockers / gates

- BF-1 PRE-P1 BLOCKER: frozen v0.1 does not define authoritative stale GitHub scale-set assignment recovery. A controller restart can observe TotalAssignedJobs>0 while incomplete JobAssigned metadata prevents authoritative job reconstruction; maxRunners=1 then wedges the lane. v0.2 must freeze fail-closed divergence detection, lane quarantine/no-new-acquisition, bounded cleanup/reset, proof of zero live/stale assignments before one replacement trigger, duplicate-trigger suppression, receipts, and restart recovery tests without merely raising maxRunners.
- BF-2 PRE-P1 DESIGN BLOCKER: frozen v0.1 does not define bounded owner-restricted privileged maintenance/recovery authority. v0.2 must freeze an allowlisted maintenance command surface with exact trusted identity/blob checks, root-side validation, durable receipts and rollback, no arbitrary shell/path/systemd-property authority, no untrusted/fork invocation, and no circular dependence on the L1 fleet as its own sole repair authority.

## Temporary infrastructure debt

- `workspace-control` remains temporarily public.
- `research-engine` remains private.
- Exact-provenance validation transport still uses the healthy research-engine GPU listener while root execution authority remains CPU-only.
- Do not retire those paths until reviewed replacements are live and rollback-safe.

## Heartbeat status

Workspace Heartbeat was attempted and retried with the real task ID, but the connector/tunnel returned HTTP 403. Work therefore continued from durable GitHub state as authorized; no replacement task ID or invented heartbeat state was created.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
