<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-operator-bridge-implementation-v1
- Status: IN_PROGRESS
- Current stage: impl_09_performance_benchmark_execution

## Current verified state

- Exact head `8d50ef0b87b85480d10452d88965a0a616e2c2af` passed Workspace Control Validation #2474 and Operator Bridge Validation #105.
- Isolated target-preflight job `129889811928` / run `42833594686` passed: `TARGET_ADAPTER_PREFLIGHT`, `FIREFOX_EXTENSION`, adapter version `0.1.9-perf`.
- Full target attempt run `42834251364` / job `129894144174` failed before UX-09 measurements at the adapter preflight and produced no `stage09-target-evidence.json`.
- Immediate isolated reproduction run `42835407614` / job `129896159398` also failed.
- Failure artifact `13773931227` reports `ADAPTER_CONNECTION_NOT_OBSERVED`; helper was enabled, Firefox launcher exited cleanly, runner exit code was 0, and zero Firefox processes remained. No adapter identity rejection occurred.
- Diagnostic code head `544911b724aa0c943786a285a6e38213a861667e` adds bounded Firefox `extensions.json` runtime-state verification for only the expected signed adapter fields.
- Queued diagnostic target-preflight job: `129899072941`.

## Current blocker

The signed 0.1.9 performance adapter stopped connecting after a previously successful isolated launch. The unresolved distinction is now:
1. Firefox has disabled/deactivated the installed signed adapter in the dedicated `WorkspaceWorkers` profile; or
2. the adapter remains active but Firefox MV3 background/event-page startup/wake behavior or abrupt owned-process shutdown prevents the background script from connecting on subsequent launches.

This is no longer an identity-mismatch or leaked-process problem.

## Next safe action

Start or keep an interactive Windows self-hosted runner labeled `workspace-operator-target` listening so queued job `129899072941` can execute against exact diagnostic head `544911b724aa0c943786a285a6e38213a861667e`.

If runtime state reports the adapter inactive/disabled, repair only the dedicated Stage-09 signed-add-on install state and rerun isolated preflight. If it reports active/enabled yet connection is still absent, investigate MV3 wake/startup and graceful owned Firefox shutdown. Preserve exact-head Native Messaging binding, fake-worker-only behavior, `ADAPTER_IDENTITY_REJECTED`, process ownership, and content-free evidence.

Do not rerun the full Stage-09 matrix until isolated preflight is PASS again. Do not begin impl_10+.
