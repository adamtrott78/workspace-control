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
- Current stage: independent_preimplementation_review

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, per-project isolation, fail-closed admission, review gates, and a clean path to GitHub organization runner groups. Reduce operator copy/paste by making review targets and dispositions durable and GitHub-native.

## Exact frozen review target

- Architecture: `architecture/github-actions-selfhosted-control-plane.v0.1.json@f70f100ba57140469ff656255de00f7de262dbc3`
- NOT_INSTALLED workspace-control manifest: `architecture/lambda-ci-project-workspace-control.v1.json@efa6e09f4206ca1d1d2fe6daaabcb69ed01d4588`
- Review instructions: `.github/instructions/selfhosted-control-plane.instructions.md@e91e6179adb636a58f8518ce71c58a6f348e994b`

No live registry, controller, workflow target, systemd, or Lambda host state was activated by this design tranche.

## Core architecture

1. **L0 stable bootstrap** — independently recoverable authority that can validate/recover control-plane policy without depending on the dynamically reconciled fleet.
2. **L1 control JIT** — bounded ephemeral/JIT workspace-control validation, initially owner-commanded and concurrency 1.
3. **L2 project JIT** — existing research-engine/PADataset CPU/GPU project identities and isolation.

The long-term GitHub organization target uses runner groups restricted by selected repository and, where supported, exact trusted workflows. GitHub-side centralization does not collapse project-specific Unix/filesystem identities.

## Resource target

Initial future control lane: concurrency 1, about 200% CPU, MemoryHigh about 4G, MemoryMax about 8G, no GPU, short runtime. Current project/lane controller hard-cap remains one runner; excess demand queues rather than creating unbounded simultaneous jobs.

## Review surface

- PR #508, initial frozen design-review head `ff8515b59070b8761e5f78db633e359395880196`.
- Copilot review was requested via GitHub REST, but no reviewer/review is currently visible; independent review remains unsatisfied.
- Hosted validation run `40249868676` / job `121339210627` failed before runner execution with `steps=null`: `VALIDATION_UNAVAILABLE`, not design failure.

## Resource audit

The generic provisioner currently uses one process-global `_active` set and current project manifests use `concurrency: 1`, so generic execution is effectively host-wide serialized. Moving control jobs onto Lambda therefore increases queue depth/latency, not simultaneous host load, unless a later reviewed scheduler change deliberately permits parallelism.

## Next safe action

On PR #508, obtain an independent review of the exact frozen design and manifest. Verify bootstrap non-circularity, public-window containment, control isolation/resource bounds, current global serialization/queue implications, staged automatic-event admission, staged organization migration, and non-self-approving review automation. **Do not activate the workspace-control runner before disposition.**

Separately, when temporary public visibility or hosted capacity is actually active, rerun authoritative reconciliation `40243005403` to unblock current EXTRACT validation without changing scientific authority.

## Remaining work

- Obtain and durably consume independent review of exact v0.1 design/manifest.
- Restore the currently blocked reconciliation/EXTRACT validation chain using the temporary emergency capacity workaround.
- After NO_BLOCKING_FINDING, implement and validate the P1 owner-commanded workspace-control JIT pilot without moving bootstrap reconciliation authority.
- Design/review control-small and automatic pull_request/push admission as P2.
- Migrate routine hosted CI only after the pilot and automatic-event gates pass.
- Evaluate and separately execute GitHub organization migration with runner groups and least-privilege GitHub App credentials.
- Automate routine review request/consumption so the operator does not ferry text between chats.

## Blocker / gate

Live workspace-control self-hosted activation is blocked pending independent review of the exact v0.1 design/manifest.

## Emergency unblock incident — 2026-10-26

- Temporary public visibility on `workspace-control` restored GitHub-hosted reconciliation while `research-engine` returned private.
- The exact-provenance implementation gate reached real Lambda execution; the original workflow and `cpu-test` systemd profiles both had 30-minute ceilings, so the job was terminated during contract tests.
- Both infrastructure ceilings were widened to 60 minutes without changing the frozen design, implementation candidate, benchmark, or scientific authority.
- Recovery exposed a controller reliability defect: `maxRunners=1` plus stale GitHub assigned-job bookkeeping can poison a lane after runner termination/restart, and duplicate recovery triggers make that queue state worse.
- The exact-provenance validation route is temporarily transported through the healthy research-engine GPU scale-set listener while the root execution contract remains `cpu-public-ci-v1` / `cpu-test` / GPU count 0.
- The validation-only contract-test step is now network-free and executes the same 31 no-argument contract tests without `pip install`; trusted workflow blob `ac03ea6196ae1b427e5f3c608e5ce5fb18704e1e` is reconciled.
- Permanent control-plane work must include stale-assignment recovery, reviewed resource-aware concurrency instead of hard-coded/global serialization, and trusted remote maintenance actions so routine recovery does not require operator shell copy/paste.

## Immediate next safe action

Do not create duplicate exact-provenance validation runs. Wait for superseded run `40266278120` to become terminal. Then issue exactly one validation for candidate `3eb6b391fcd2f6e2a44277771d0bcd8d26c7002d` using the reconciled network-free workflow and require terminal implementation-validation PASS before authorizing the single preregistered scientific trigger.

## Fresh-chat initialization

@GitHub @Heartbeat

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json`

Task ID:

`workspace-github-actions-selfhosted-control-plane-v1`

Start from the normal workspace-control root route.
Treat the authoritative task capsule, synchronized Markdown handoff, exact durable Git/runtime state, and referenced evidence as the complete handoff.
Do not rely on previous conversation state.
Immediately begin Workspace Heartbeat with the same real task ID.
Follow the capsule's `next_safe_action`.
Do not mutate Local EXTRACT science.
Do not activate a self-hosted control runner until the exact design receives independent review.
