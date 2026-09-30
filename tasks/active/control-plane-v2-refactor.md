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
- Status: `CHECKPOINTED`

## Goal

Design, implement, and validate a workspace-control v2 architecture that generalizes the proven tutor, Codex, DIRECT_TOOL, human-gate, and PADataset/MILCOM workflow evidence into an executor-neutral, resumable multi-stage control plane without moving project-domain authority out of project repositories.

## Current target

- Repository: `workspace-control`
- Branch: `control-plane-v2-refactor`
- Base: `cb8368cd50de2d364c2aade8843276aab0b02420`
- Current checkpoint: `610c71902425adaf054fc9ba13deb21bba7cc7ce`
- Pushed: `true`

### Allowed mutation scope

- `architecture/control-plane-v2.md`
- `architecture/control-plane-v2-implementation.md`
- `schemas/task_capsule.v1.schema.json`
- `schemas/task_capsule.v2.schema.json`
- `schemas/workflow_descriptor.v1.schema.json`
- `tests/test_workspace_control.py`
- `tests/fixtures/**`
- `README.md`
- `policies/PORTABILITY_CONTRACT.md`
- `policies/OPERATOR_WORKFLOW.md`
- `policies/TUTORING_CONTRACT.md`
- `templates/COURSE_TUTOR_ADAPTER.md`
- `procedures/TUTOR_EVALUATION.md`
- `schemas/task_capsule.schema.json`
- `scripts/workspace_control.py`
- `procedures/task_capsule.md`
- `tasks/README.md`

## Next safe action

On control-plane-v2-refactor@610c71902425adaf054fc9ba13deb21bba7cc7ce, modify only scripts/workspace_control.py, schemas/task_capsule.schema.json, procedures/task_capsule.md, tasks/README.md, and existing tests/fixtures as needed to add schema-version dispatch, v2 task validation, and deterministic task-render. Preserve all existing v1 command behavior. Do not change preflight or handoff semantics in this phase.

## Remaining work

- Implement Phase 4 schema-version dispatch, v2 task structural/semantic validation, deterministic task-render, and supporting task-capsule documentation/tests without changing preflight/handoff behavior yet.
- Run v1 compatibility tests plus v2 validation/render fixtures in a real runtime before declaring Phase 4 complete.
- Only after Phase 4 passes, open topology-aware preflight scope.

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
- **V2 implementation plan reviewed:** `PASS`
  - architecture/control-plane-v2-implementation.md reviewed through control-plane-v2-refactor@5000900823150676d356c54642efdefc560878ca
  - Review preserved exact shared-contract pins, optional workflow descriptors, deferred project adoption, and derived handoff synchronization.
- **Phase 2 exact changed-path set:** `PASS`
  - Compare 5000900823150676d356c54642efdefc560878ca...bb4292d65e858ec2fd527c8984a769e4bb87f955 reports exactly the three schema paths, one test file, and five fixture files authorized for Phase 2.
- **V1 schema compatibility copy:** `PASS`
  - schemas/task_capsule.schema.json and schemas/task_capsule.v1.schema.json both resolve to Git blob 40fa76125f61c0ad8e11a10a45347dbb36c63a84 at bb4292d65e858ec2fd527c8984a769e4bb87f955.
- **Phase 2 JSON schema/fixture parse:** `PASS`
  - All three schema files and all five JSON fixtures were independently reread from bb4292d65e858ec2fd527c8984a769e4bb87f955 and parsed successfully.
- **Python Phase 2 unittest execution:** `NOT_RUN`
  - No local/runtime executor has executed tests/test_workspace_control.py yet; source/fixture validation is recorded separately and does not imply test-run success.
- **Phase 3 exact changed-path set:** `PASS`
  - Compare bb4292d65e858ec2fd527c8984a769e4bb87f955...610c71902425adaf054fc9ba13deb21bba7cc7ce reports exactly six authorized contract/routing files.
- **Phase 3 stale executor/bridge language scan:** `PASS`
  - All six Phase 3 files were reread from 610c71902425adaf054fc9ba13deb21bba7cc7ce.
  - No stale 'Codex vs ChatGPT-assisted human' framing, bridge-v0.1 heading, or old 'Execution modes' heading remained.
- **Phase 3 project-domain authority boundary:** `PASS`
  - README and operator contract explicitly preserve project-local truth.
  - Tutoring contract explicitly states course repositories retain authority for syllabus, assignments, instructor material, notation, deliverables, grading rules, and topic structure.

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

Treat the task capsule, normal workspace-control root route, exact Git state, and durable evidence referenced by the capsule as the handoff.

Do not rely on previous conversation state.

Follow the capsule's next_safe_action.

Current target branch:
control-plane-v2-refactor

Current target checkpoint:
610c71902425adaf054fc9ba13deb21bba7cc7ce

Do not broaden mutation scope beyond the capsule.
```
