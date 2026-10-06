# Lambda/GitHub Tooling Optimization Inventory v1

Status: evidence checkpoint; no shared runtime behavior changed.

## Current control-plane state

- workspace-control main: `d6f1b02ddd8f611ab99b908123c0e5e5ef59d29a`
- research-engine main: `72e3e16ca118c4756c528392158738a39cb5d5aa`
- research-engine P3 run `37398604653`: queued on `cpu-test-v2`
- parent acceptance remains authoritative for P3/P4/P5.

## Measured launcher duplication

The current P2-B and P3 JIT launchers are structural copies:

- both are 427 lines;
- 405/427 lines are identical at the same positions (94.8%);
- both define exactly the same nine functions:
  `run`, `require_clean_identity`, `verify_host_foundation`,
  `primary_subnet`, `github_jit_config`, `chown_tree`,
  `systemd_command`, `collect_diag`, and `main`;
- the only top-level constant difference is
  `MAX_RUNTIME_SECONDS=900` versus `2100`.

All other observed differences are phase/profile metadata:

- runner label `cpu-test` versus `cpu-test-v2`;
- authorization environment variable name;
- runner/unit/job/output naming;
- receipt phase/file/message text;
- timeout/error wording.

This is control-plane duplication, not project-domain behavior.

## Existing reusable policy sources

### Project manifest

`architecture/lambda-ci-project-research-engine.v1.json` already owns:

- repository identity;
- project runner user/group;
- jobs/staging/trusted-cache/log roots;
- forbidden paths;
- CPU/GPU resource profiles;
- runtime limits;
- GPU indices;
- public-egress / production-service policy;
- repository checkout permission constraints;
- project concurrency.

### Systemd profiles

`architecture/lambda-ci-systemd-profiles.v1.json` separately owns:

- common systemd hardening;
- capability denial;
- filesystem protections;
- process/cgroup cleanup behavior;
- device policy;
- cache/home environment;
- CPU/memory/task/runtime limits;
- GPU device candidates.

The phase-specific launchers currently repeat substantial portions of those policies instead of consuming one authoritative profile representation.

### Provisioner protocol

`architecture/lambda-ci-provisioner-protocol.v1.md` already describes the desired generic privilege boundary:

`project_id + profile + runner_name + jit_config`

Privilege-bearing filesystem/device/network/systemd values are resolved from root-owned manifests, not accepted from the controller.

## Dependency/bootstrap boundary

`scripts/bootstrap_lambda_ci_p3_postgres_runtime.sh` is materially different from the JIT lifecycle. It is a bounded, receipt-producing project dependency bootstrap for exact PostgreSQL 14.24 + pgvector 0.8.6.

It should therefore become a **profile/project dependency prerequisite**, not logic inside a generic global launcher.

Required invariant:

- project/profile declares an exact dependency identity;
- dependency preflight/bootstrap is bounded and idempotent;
- receipt proves exact source/version and production-state non-mutation;
- JIT launch refuses the profile when the prerequisite receipt/runtime is absent or mismatched.

## Proposed reusable boundaries

1. **Execution profile schema**
   - project/repository identity
   - profile name and runner labels
   - exact resource/device/network/filesystem policy
   - bounded runtime
   - dependency prerequisites
   - receipt contract
   - denied capabilities

2. **Generic one-job JIT launcher**
   - token prompt/use-in-process only
   - GitHub JIT config generation
   - exact manifest/profile lookup
   - fresh job tree
   - systemd launch
   - bounded wait
   - diagnostics
   - leaked-process cleanup
   - workspace destruction
   - non-secret receipt

3. **Project dependency bootstrap adapters**
   - PostgreSQL/pgvector remains research-engine-specific
   - future dependencies declared per project/profile
   - no global pgvector assumption

4. **Evidence-consumption loop**
   - dispatch/runner/run/artifact identifiers in compact receipt
   - terminal GitHub status consumed immediately
   - no thought/wait loop after terminal state

## Baseline operator-friction observations

Current P3 acceptance still requires two human-only operations:

1. privileged runtime bootstrap;
2. hidden short-lived repository Administration:write token entry for the JIT launcher.

Those gates are intentionally preserved until the parent task accepts a narrower durable mechanism. Optimization should reduce repeated shell/code glue around them without silently broadening authority.

## Next design step

Define the versioned execution-profile contract and executable regression matrix first. Then replace P2-B/P3 phase-specific launcher copies with one generic launcher while proving behavior equivalence for:

- no personal credential exposure;
- no Docker/sudo access in candidate job;
- exact project UID isolation;
- production-service denial;
- resource/device/network policy;
- one-job JIT destruction;
- leaked-process detection;
- compact cleanup receipt.
