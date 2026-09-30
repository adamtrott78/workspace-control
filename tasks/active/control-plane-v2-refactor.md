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
- Current checkpoint: `77c7355bbafeb674dd35b55bcfdb542d50c6079c`
- Pushed: `true`

### Allowed mutation scope

- `scripts/workspace_control.py`
- `procedures/repo_preflight.md`
- `tests/test_workspace_control.py`
- `tests/fixtures/**`

## Next safe action

Begin Phase 5 only. Starting from control-plane-v2-refactor@77c7355bbafeb674dd35b55bcfdb542d50c6079c, implement topology-aware preflight within scripts/workspace_control.py, procedures/repo_preflight.md, tests/test_workspace_control.py, and tests/fixtures/**. Preserve the existing preflight invocation as backward-compatible local behavior; add explicit remote topology support without creating a local checkout; model composed work as explicit remote/local checks plus a synchronization boundary rather than one opaque hybrid preflight. Inspect and validate the exact changed-path set before runtime testing. Do not begin topology-aware handoff or worktree-preparation implementation yet.

## Remaining work

- Implement Phase 5 topology-aware preflight while preserving the existing local preflight invocation and semantics.
- Add explicit remote topology preflight that validates registry identity, expected remote/ref/SHA, writable policy, mutation scope, expected parent when supplied, and operation capability/authorization without manufacturing a local checkout.
- Add composed-transition checks sufficient to prove remote and local identities and their synchronization boundary without assuming remote mutation updated local state.
- Update procedures/repo_preflight.md and add bounded tests/fixtures for local backward compatibility, remote expected-SHA match/mismatch, non-writable repositories, isolated task branches, and composed synchronization assumptions.
- Run source/diff validation first, then bounded real-runtime validation before opening Phase 6 topology-aware handoff scope.

## Latest completed runtime gate

- `PHASE4_RUNTIME_RESULT=PASS`
- `VALIDATED_COMMIT=77c7355bbafeb674dd35b55bcfdb542d50c6079c`
- v2 capsule is explicitly refused by v1 handoff semantics.
- Existing workspace worktrees were not switched, cleaned, reset, stashed, or modified.

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

## Blockers / known limitations

- None recorded.

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
77c7355bbafeb674dd35b55bcfdb542d50c6079c

Current phase:
Phase 5 — topology-aware preflight

Do not broaden mutation scope beyond the capsule. Do not begin topology-aware handoff or worktree-preparation implementation until Phase 5 is validated and checkpointed.
```
