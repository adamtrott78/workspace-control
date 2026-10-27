<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: `tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json`

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: `workspace-github-actions-selfhosted-control-plane-v1`
- Title: GitHub Actions Self-Hosted Control Plane v1
- Status: `IN_PROGRESS`
- Current stage: `independent_preimplementation_review`
- Control-plane review surface: workspace-control PR #508
- Frozen design blob: `f70f100ba57140469ff656255de00f7de262dbc3`
- NOT_INSTALLED workspace-control manifest blob: `efa6e09f4206ca1d1d2fe6daaabcb69ed01d4588`

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, project isolation, fail-closed admission, review gates, and a later reversible GitHub-organization/runner-group migration. Routine recovery should also stop requiring the operator to paste privileged shell commands.

## Exact current state

- `workspace-control` main: `fec659a6d75e44c56acc53b706290b248681b584`
- `research-engine` main: `0badc99b894d87413d065afdcd37a678c2839007`
- `workspace-control` is still temporarily **public** for emergency hosted-capacity recovery.
- `research-engine` is **private**.
- There were zero live research-engine Actions runs when this handoff was hydrated.
- PR #508 remains open and design-only. No independent review submission exists yet.
- PR #514 merged a state-consistency-only repair for the separate EXTRACT owner task so repository task validation is clean again.
- Frozen v0.1 architecture/manifest blobs have not changed.
- PR #508 runtime-evidence comments:
  - `6405597751` — organization-migration implementation audit.
  - `6408089808` — observed queue poisoning, global serialization, transport/execution separation, and operator-shell burden.

## P0 emergency unblock — COMPLETE

The EXTRACT execution blockage that originally forced the emergency public-repository workaround is no longer a blocker for this control-plane task.

- Mandatory implementation validation: run `40269453984`, workflow-local run 14, job `121398888450`, artifact `12626998979` — **PASS**, including `31/31` contract checks.
- Exactly one authorized scientific execution: run `40411159582`, workflow-local run 16, job `121881887321`, artifact `12693836542` — execution **PASS**.
- Scientific interpretation of that result is owned by the separate task `workspace-local-extract-independent-review-v1`.
- Do **not** continue EXTRACT science inside this GitRunner/control-plane task.
- Temporary exact-provenance validation transport still uses the healthy research-engine GPU scale-set listener while root execution authority remains `cpu-public-ci-v1` / `cpu-test` / GPU count 0. This is cleanup debt, not the target architecture.

## Observed control-plane defects that must survive the handoff

- `maxRunners=1` made a stale GitHub scale-set assignment capable of wedging an entire lane.
- After controller restart, GitHub can report assigned-job count without replaying enough authoritative per-job metadata for Admission-v2 recovery.
- Creating replacement runs before proving the stale queue empty amplifies queue poisoning.
- Generic provisioner host-wide `_active` plus project `concurrency: 1` effectively serializes unrelated workloads.
- Routine controller restart/profile installation required too much operator shell intervention.
- Transport identity and execution authority are separable: a CPU-only route can be carried over another healthy listener without granting GPU execution authority, provided root admission remains exact and fail-closed.

These are review inputs. They do not automatically authorize implementation changes beyond the reviewed phase.

## Next safe action

Perform the **independent preimplementation review of PR #508** against the exact frozen v0.1 architecture and NOT_INSTALLED workspace-control manifest, explicitly incorporating comments `6405597751` and `6408089808`.

Persist either:

- `NO_BLOCKING_FINDING`, or
- exact blocking findings.

Do **not** activate a workspace-control runner before that disposition.

If the review is clean, implement **only P1**: the owner-commanded workspace-control JIT CPU validation pilot, while leaving bootstrap reconciliation authority independent.

If the runtime evidence blocks v0.1, revise/freeze a bounded v0.2 and re-review before implementation.

## Remaining work

- Obtain and durably consume independent review of exact v0.1 design/manifest plus incident evidence.
- Decide whether stale-assignment recovery, single-slot queue poisoning, host-wide serialization, and operator-shell recovery require a v0.2 design before P1.
- After accepted review, implement and validate the P1 owner-commanded workspace-control JIT pilot without moving bootstrap authority.
- Design/review `control-small` and automatic `pull_request` / trusted default-branch admission as P2.
- Replace hard-coded `maxRunners=1` and host-wide global serialization only through separately reviewed bounded/resource-aware concurrency.
- Add owner-restricted trusted remote maintenance/recovery actions so routine controller restart/profile installation does not require operator copy/paste.
- Migrate routine hosted CI only after pilot and automatic-event gates pass.
- Separately design/review GitHub organization migration, runner groups, owner-qualified identity changes, and least-privilege GitHub App auth.
- Retire temporary public workspace-control and GPU-listener transport workarounds only after a reviewed replacement is live and rollback-safe.

## Blocker

Live workspace-control self-hosted activation is blocked pending independent review of the exact v0.1 design/manifest **plus** the post-freeze runtime incident evidence on PR #508.

## Fresh-chat initialization

Use GitHub and Workspace Heartbeat.

Repository:

`https://github.com/adamtrott78/workspace-control`

Task ID:

`workspace-github-actions-selfhosted-control-plane-v1`

Start from the normal workspace-control root route.

Treat the authoritative task capsule, this synchronized Markdown handoff, PR #508, exact frozen design/manifest blobs, current main state, and runtime-evidence comments as the complete handoff.

Do not rely on previous conversation state.

Do not switch into `workspace-local-extract-independent-review-v1`; that is a separate scientific-review lane.

Follow the capsule's `next_safe_action`.
