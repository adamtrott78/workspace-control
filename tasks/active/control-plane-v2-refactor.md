# Workspace Control Plane v2 — Current Handoff

> **Derived human-readable view.**
>
> Authoritative task state: `tasks/active/control-plane-v2-refactor.json` on `control-plane-v2-coordination`.
>
> If this file disagrees with the JSON capsule or verified Git/runtime state, trust the JSON capsule plus verified evidence.
>
> Regenerate this view whenever the capsule materially changes.

## Task

- ID: `control-plane-v2-refactor`
- Title: Workspace Control Plane v2
- Status: `VALIDATING`

## Goal

Design, implement, and validate a workspace-control v2 architecture that generalizes the proven tutor, Codex, DIRECT_TOOL, human-gate, and PADataset/MILCOM workflow evidence into an executor-neutral, resumable multi-stage control plane without moving project-domain authority out of project repositories.

## Current target

- Repository: `workspace-control`
- Branch: `control-plane-v2-refactor`
- Base: `cb8368cd50de2d364c2aade8843276aab0b02420`
- Current checkpoint: `5a7a4fa331a25568490ead42156dea1f2a5c52b6`
- Pushed: `true`

### Allowed mutation scope

- `architecture/control-plane-v2.md`
- `architecture/control-plane-v2-implementation.md`

## Next safe action

Review architecture/control-plane-v2-implementation.md at control-plane-v2-refactor@5a7a4fa331a25568490ead42156dea1f2a5c52b6. Do not authorize Phase 2 schema/test mutations until the plan's compatibility strategy, file map, phase ordering, and regression gates are accepted.

## Remaining work

- Review architecture/control-plane-v2-implementation.md against its ten review questions and the reviewed architecture baseline.
- After implementation-plan approval, expand target mutation scope only to Phase 2 compatibility scaffolding: v1/v2 capsule schemas, workflow descriptor schema skeleton, tests, and fixtures.
- Establish v1 schema equivalence and fixture coverage before changing scripts/workspace_control.py.
- Then integrate shared contracts, add schema-version dispatch/task-render, topology-aware preflight/handoff, safe worktree preparation, workflow descriptor validation, and thin Codex adapters in gated phases.
- Run the full regression matrix, including remote-only, local, composed, human-gate, idempotent, failure-recovery, and both Codex/ChatGPT handoff directions.
- Only after validation, decide promotion to main and later PADataset migration.

## Validation state

- **Preserved evidence branches verified before v2 initialization:** `PASS`
  - GitHub branch endpoints matched the expected main, shared bridge, Codex target, and Phase-4 coordination SHAs.
- **New v2 branches created from exact baseline:** `PASS`
  - Both control-plane-v2-refactor and control-plane-v2-coordination were created from cb8368cd50de2d364c2aade8843276aab0b02420.
- **V2 architecture specification reviewed:** `PASS`
  - architecture/control-plane-v2.md reviewed and refined through control-plane-v2-refactor@07075963f2d56f1bf76d562de3f6a6dc0d16c43d
  - Review resolved authority-owner vs execution-owner ambiguity, workflow version binding, checkpoint bundles, HANDOFF_SAFE vs EXECUTION_READY, artifact lifecycle overlap, generated handoff authority, secret handling, consequence classes, and coordination-state placement.
- **Integrated v2 implementation validated:** `NOT_RUN`
- **Cross-executor regression suite completed:** `NOT_RUN`
- **Initial v2 architecture draft created within authorized target scope:** `PASS`
  - Target branch changed only by architecture/control-plane-v2.md at 93c7cbbd82ed9d46e43c2ad38a57ba81165e8f3e.
- **Architecture branch remained within authorized review scope:** `PASS`
  - Compare cb8368cd50de2d364c2aade8843276aab0b02420...07075963f2d56f1bf76d562de3f6a6dc0d16c43d shows only architecture/control-plane-v2.md changed.
- **Implementation plan created within authorized planning scope:** `PASS`
  - Only architecture/control-plane-v2.md and architecture/control-plane-v2-implementation.md are authorized target paths at this stage.

## Blockers / known limitations

- The v1 HANDOFF_SAFE checker is local-worktree-centric. This capsule is durable remote coordination state, but formal v1 HANDOFF_SAFE validation requires an isolated local worktree at the recorded checkout path. Do not confuse this known v1 checker limitation with loss of the remote task state.

## Fresh-chat initialization

```text
@GitHub

Continue the durable workspace-control task defined by:

Repository:
adamtrott78/workspace-control

Coordination branch:
control-plane-v2-coordination

Task capsule:
tasks/active/control-plane-v2-refactor.json

Treat the task capsule, the normal workspace-control root route, exact Git state, and the durable evidence referenced by the capsule as the handoff.

Do not rely on previous conversation state.

Follow the capsule's next_safe_action.

Current target branch:
control-plane-v2-refactor

Current target checkpoint:
5a7a4fa331a25568490ead42156dea1f2a5c52b6

Do not broaden mutation scope beyond the capsule.
```
