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
- Status: `BLOCKED_RUNTIME`

## Goal

Design, implement, and validate a workspace-control v2 architecture that generalizes the proven tutor, Codex, DIRECT_TOOL, human-gate, and PADataset/MILCOM workflow evidence into an executor-neutral, resumable multi-stage control plane without moving project-domain authority out of project repositories.

## Current target

- Repository: `workspace-control`
- Branch: `control-plane-v2-refactor`
- Base: `cb8368cd50de2d364c2aade8843276aab0b02420`
- Current checkpoint: `01ebfed8d8b79ec1cbf52930c6f02b13eeae4386`
- Pushed: `true`

### Allowed mutation scope

- `scripts/workspace_control.py`
- `procedures/worktree_prepare.md`
- `tests/test_workspace_control.py`
- `tests/fixtures/**`

## Next safe action

Remain in Phase 7. Validate exact pushed checkpoint 01ebfed8d8b79ec1cbf52930c6f02b13eeae4386 in an isolated GitHub-connected runtime. Run the full unit suite and bounded real-Git worktree-prepare scenarios proving read-only CREATE_AVAILABLE, explicit --create -> READY at the exact checkpoint, existing READY behavior, dirty-state preservation/refusal, divergence refusal without branch movement, and non-interference with existing workspace worktrees. Record the runtime evidence, then and only then mark Phase 7 validated/checkpointed and open the next planned phase.

## Remaining work

- Run the complete Python unit suite from exact checkpoint 01ebfed8d8b79ec1cbf52930c6f02b13eeae4386 in an isolated temporary clone.
- Run worktree-prepare read-only against an isolated temporary repository and require CREATE_AVAILABLE without creating the target.
- Run the same request with --create and require READY at the exact branch/checkpoint.
- Re-run read-only assessment on the created worktree and require READY without mutation.
- Prove dirty target refusal preserves the dirty file.
- Prove divergent remote/ref state returns BLOCKED_DIVERGED without moving the local branch or deleting/rewriting the worktree.
- Verify non-interference with existing workspace worktrees.
- Only after those checks pass, mark Phase 7 validated/checkpointed and follow the implementation plan's next phase.

## Latest completed runtime gate

- `PHASE6_RUNTIME_RESULT=PASS`
- `VALIDATED_COMMIT=f88fb301ea9fd500fcfa5ee8614ce33bd64f55c9`
- Phase 7 implementation checkpoint: `01ebfed8d8b79ec1cbf52930c6f02b13eeae4386`
- Phase 7 exact-checkpoint runtime validation is pending.

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
- **Python Phase 2 unittest execution:** `PASS`
  - The Phase 4 bounded runtime validation executed tests/test_workspace_control.py successfully as part of PHASE4_RUNTIME_RESULT=PASS at 77c7355bbafeb674dd35b55bcfdb542d50c6079c.
- **Phase 3 exact changed-path set:** `PASS`
  - Compare bb4292d65e858ec2fd527c8984a769e4bb87f955...610c71902425adaf054fc9ba13deb21bba7cc7ce reports exactly six authorized contract/routing files.
- **Phase 3 stale executor/bridge language scan:** `PASS`
  - All six Phase 3 files were reread from 610c71902425adaf054fc9ba13deb21bba7cc7ce.
  - No stale 'Codex vs ChatGPT-assisted human' framing, bridge-v0.1 heading, or old 'Execution modes' heading remained.
- **Phase 3 project-domain authority boundary:** `PASS`
  - README and operator contract explicitly preserve project-local truth.
  - Tutoring contract explicitly states course repositories retain authority for syllabus, assignments, instructor material, notation, deliverables, grading rules, and topic structure.
- **Phase 4 exact changed-path set:** `PASS`
  - Compare 610c71902425adaf054fc9ba13deb21bba7cc7ce...77c7355bbafeb674dd35b55bcfdb542d50c6079c reports exactly five intended Phase 4 files.
- **Phase 4 source structure inspection:** `PASS`
  - Pushed script contains explicit v1 validator, v2 validator, schema-version dispatcher, task-render implementation/parser wiring, and an explicit guard preventing v2 capsules from being assessed with v1 handoff semantics.
- **Phase 4 Python syntax/unit/runtime validation:** `PASS`
  - Lambda runtime validation completed with PHASE4_RUNTIME_RESULT=PASS.
  - Validated exact commit 77c7355bbafeb674dd35b55bcfdb542d50c6079c.
  - v2 capsule was explicitly refused by v1 handoff semantics, proving the compatibility guard executes correctly.
  - Validation did not switch, clean, reset, stash, or modify existing workspace worktrees.
- **Phase 4 v1/v2 handoff compatibility guard:** `PASS`
  - Runtime result explicitly reported: PASS: v2 capsule is explicitly refused by v1 handoff semantics.
  - This confirms v2 task state is not silently interpreted under v1 local-only handoff rules.
- **Phase 4 runtime non-interference with existing worktrees:** `PASS`
  - Lambda reported that existing workspace worktrees were not switched, cleaned, reset, stashed, or modified.
- **Phase 5 exact changed-path set:** `PASS`
  - Compare 77c7355bbafeb674dd35b55bcfdb542d50c6079c...dc6980284abc17f4c0f96d90b01391e2c952879f reports exactly procedures/repo_preflight.md, scripts/workspace_control.py, and tests/test_workspace_control.py.
  - All changed paths are inside the capsule's authorized Phase 5 mutation scope.
- **Phase 5 topology/source contract inspection:** `PASS`
  - Default preflight topology is local and the existing local state/payload path remains in place.
  - Remote inspection calls git ls-remote against the registered remote URL and does not inspect a checkout/worktree.
  - Parser permits only local or remote topology; composed execution is documented as separate remote/local preflights plus a synchronization boundary.
- **Phase 5 bounded logic harness:** `PASS`
  - PHASE5_LOGIC_HARNESS=PASS against an isolated temporary bare remote.
  - Policy-edge harness also passed non-writable refusal and rejection of opaque composed preflight.
  - No existing workspace worktree was switched, cleaned, reset, stashed, or modified by these harnesses.
- **Phase 5 exact-checkpoint integrated runtime validation:** `PASS`
  - Exact isolated validation checkout resolved ACTUAL_HEAD=dc6980284abc17f4c0f96d90b01391e2c952879f.
  - tests/test_workspace_control.py completed 18 tests with OK.
  - Documented remote preflight returned result=READY, reasons=[], advertised status=FOUND, and advertised SHA=dc6980284abc17f4c0f96d90b01391e2c952879f.
  - Remote preflight confirmed surface_write_ready=true, consequence=reversible, and the exact Phase 5 allowed/proposed path set.
  - Validation reported PHASE5_RUNTIME_RESULT=PASS and explicitly confirmed non-interference with existing workspace worktrees.
- **Phase 6 exact changed-path set:** `PASS`
  - Compare dc6980284abc17f4c0f96d90b01391e2c952879f...f88fb301ea9fd500fcfa5ee8614ce33bd64f55c9 reports exactly procedures/task_capsule.md, scripts/workspace_control.py, tasks/README.md, and tests/test_workspace_control.py.
  - All changed paths are inside the capsule's authorized Phase 6 mutation scope.
- **Phase 6 source/contract inspection:** `PASS`
  - v1 handoff function remains intact and schema_version 1 dispatches to it.
  - Remote-only v2 handoff does not call local checkout inspection or transient live-remote query.
  - Local and composed v2 handoff paths are topology-specific.
  - Receiver readiness is represented separately as execution_readiness with NOT_ASSESSED, EXECUTION_READY, or NOT_EXECUTION_READY.
  - Regression tests cover v1 compatibility, remote-only no-local behavior, local handoff, composed synchronization, workflow binding failure, missing synchronization boundary, and HANDOFF_SAFE with NOT_EXECUTION_READY.
  - No worktree-prepare command or Phase 7 implementation was added.
- **Phase 6 exact-checkpoint integrated runtime validation:** `PASS`
  - Exact isolated checkout resolved ACTUAL_HEAD=f88fb301ea9fd500fcfa5ee8614ce33bd64f55c9.
  - tests/test_workspace_control.py completed 26 tests with OK.
  - Live remote preflight returned result=READY, reasons=[], advertised status=FOUND, and advertised SHA=f88fb301ea9fd500fcfa5ee8614ce33bd64f55c9.
  - v1 compatibility and v2 remote-only/local/composed handoff assertions all passed.
  - Workflow checkpoint binding and composed synchronization boundary assertions passed.
  - HANDOFF_SAFE remained independent from receiver-specific EXECUTION_READY.
  - Validation reported PHASE6_RUNTIME_RESULT=PASS and explicit non-interference with existing workspace worktrees.
- **Phase 7 exact changed-path set:** `PASS`
  - Compare f88fb301ea9fd500fcfa5ee8614ce33bd64f55c9...01ebfed8d8b79ec1cbf52930c6f02b13eeae4386 reports exactly procedures/worktree_prepare.md, scripts/workspace_control.py, and tests/test_workspace_control.py.
  - All changed paths are inside the capsule's authorized Phase 7 mutation scope.
- **Phase 7 source/contract inspection:** `PASS`
  - worktree-prepare command is registered and requires an absolute target path, branch, and exact checkpoint.
  - Missing safe worktrees return CREATE_AVAILABLE unless --create is explicitly supplied.
  - The worktree-preparation implementation contains no fetch, reset, stash, or checkout normalization command.
  - Only git worktree add is used for the bounded creation mutation.
  - Post-failure and post-success target state are explicitly re-inspected.
  - Occupied broken symlink targets are detected instead of being hidden by path resolution.
  - Real Git tests cover the Phase 7 creation, dirty, divergence, identity, and policy gates.
- **Phase 7 exact-checkpoint integrated runtime validation:** `NOT_RUN`
  - Target implementation is pushed at 01ebfed8d8b79ec1cbf52930c6f02b13eeae4386.
  - Exact-checkpoint unit/CLI runtime validation is pending in an isolated GitHub-connected terminal.
  - Do not open the next implementation phase until this validation passes and is recorded.

## Blockers / known limitations

- Exact-checkpoint Phase 7 integrated runtime validation is pending for control-plane-v2-refactor@01ebfed8d8b79ec1cbf52930c6f02b13eeae4386.

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

Human-readable handoff:
tasks/active/control-plane-v2-refactor.md

Treat the JSON capsule, normal workspace-control root route, exact Git state, and durable evidence referenced by the capsule as authoritative. The Markdown handoff is a derived convenience view.

Do not rely on previous conversation state.

Follow the capsule's next_safe_action.

Current target branch:
control-plane-v2-refactor

Current target checkpoint:
01ebfed8d8b79ec1cbf52930c6f02b13eeae4386

Current phase:
Phase 7 — worktree preparation (runtime validation pending)

Do not broaden mutation scope beyond the capsule.
```
