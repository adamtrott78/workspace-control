# Generic Lambda CI Launcher Design v1

Status: design checkpoint; no runtime behavior changed.

## Objective

Replace the phase-specific P2-B/P3 JIT launcher copies with one profile-driven one-job launcher while preserving the exact security invariants already accepted by the parent Lambda runner task.

The measured baseline is unusually strong: the two current launchers are both 427 lines, share the same nine functions, and are 94.8% identical line-for-line. Their meaningful differences are metadata and policy inputs, not lifecycle mechanics.

## Contract boundary

The generic launcher consumes a validated root-owned execution-profile document conforming to:

`architecture/lambda-ci-execution-profile.v1.schema.json`

The launcher request is intentionally small:

- project ID
- profile name
- opaque run ID / runner name
- JIT configuration supplied only in memory/stdin

Repository, UID/GID, filesystem roots, labels, runtime/resource/device/network policy, dependency prerequisites, and receipt format are resolved from the trusted profile. They are not caller-supplied privilege inputs.

## Generic launcher responsibilities

1. verify root/sudo operator context and explicit authorization gate;
2. load and validate one exact project/profile;
3. assert project UID is idle and foundation paths are present;
4. verify declared dependency prerequisites;
5. prompt for the short-lived repository-scoped JIT credential;
6. request one GitHub JIT configuration;
7. create one fresh job/runner tree;
8. launch the pinned runner under the profile-derived sandbox;
9. pass JIT material only over stdin/in-process;
10. bound runtime and terminate the whole cgroup on timeout;
11. collect diagnostics;
12. kill leaked project-UID/GPU processes if required;
13. destroy the mutable runner/job tree;
14. emit a non-secret receipt;
15. return failure if cleanup invariants fail.

## What stays project-specific

The PostgreSQL 14.24 + pgvector 0.8.6 runtime bootstrap is not generic launcher logic.

For research-engine, the profile declares that dependency as an exact prerequisite. The dependency adapter remains independently bounded, idempotent, receipt-producing, and version-pinned.

Future projects may declare different dependency IDs or no dependency.

## Policy ownership

One source of truth should own each policy dimension:

- execution-profile document: repository/project/profile identity and policy;
- generic launcher: lifecycle implementation only;
- dependency adapter: exact dependency bootstrap/verification only;
- trusted repository workflow: candidate SHA/workflow-specific test logic;
- parent task capsule: authorization and acceptance state.

The launcher must not duplicate resource policy that is already represented in the execution profile.

## Migration compatibility

Initial refactor must support the current P2-B and P3 behavior as two profiles:

- P2-B compatibility profile: `cpu-test`, 900-second outer launcher bound;
- P3 compatibility profile: `cpu-test-v2`, 2100-second outer launcher bound plus exact isolated PostgreSQL/pgvector dependency prerequisite.

No current launcher is deleted until equivalence tests pass.

## Executable regression matrix

Static assertions are insufficient for privilege-boundary orchestration. The refactor requires executable tests covering:

| Area | Required executable evidence |
| --- | --- |
| profile validation | malformed/unknown project/profile rejected before JIT request |
| token handling | token absent from argv/env/files/receipt and cleared after JIT request |
| JIT request | labels/repository/group/API version come only from validated profile |
| sandbox command | generated systemd properties exactly match fixture profile |
| dependency gate | missing/mismatched dependency blocks launch before JIT execution |
| runtime bound | timeout stops/kills full transient unit |
| cleanup | leaked project-UID process causes fail-closed cleanup result |
| workspace | runner/job tree removed after success and failure |
| receipt | contains non-secret project/profile/runner/cleanup evidence only |
| P2-B equivalence | generic fixture reproduces accepted P2-B lifecycle semantics |
| P3 equivalence | generic fixture reproduces accepted P3 lifecycle semantics |
| cross-project denial | second project fixture cannot select research-engine paths/UID/dependencies |

## Operator-friction target

The initial refactor should reduce:

- two ~427-line launchers to one implementation plus declarative profiles;
- phase-specific command memorization to one launcher command with project/profile;
- duplicated receipt/cleanup fixes to one code path;
- diagnosis of policy drift by making profile differences explicit data.

The human-only JIT token and root authorization gates remain until separately accepted by the parent task; this refactor does not widen authority to remove them.
