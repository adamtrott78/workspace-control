<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-autonomous-scientific-execution-v1
- Title: PADataset autonomous scientific execution v1
- Status: IN_PROGRESS
- Current stage: live_activation
- Capsule schema: v2

## Promoted Stage-5 state

- Workspace Control main: `dff9024e16f36767facd3cbbbf1009f62b9899f7`
- Stage-5 validated PR head: `e1705197c40ee4614f6780e6872c6d0bbf6148d5`
- Normal validation: Workspace Control Validation #2600 — SUCCESS
- Authoritative validation: Lambda CI Workspace Control Validation #474 — SUCCESS on the same requested SHA
- Merge: PR #614 → `dff9024e16f36767facd3cbbbf1009f62b9899f7`
- Post-merge Project Reconcile #36 — SUCCESS
- Additive activation design commit: `46f6b048b93014d24254be232bb3e17f8e0a900d`

No live scientific class/controller/route activation has occurred.

## Additive activation design

The original v2→v3 production cutover is historical and MUST NOT be replayed.

Phase A expands the shared provisioner to the reviewed ten-class policy while:
- all pre-existing class root envelopes remain unchanged;
- existing class controllers remain running and are not restarted;
- only the shared provisioner is quiesced/restarted after zero-active/held-record and zero-transient proof;
- the scientific class is installed but INACTIVE;
- the scientific route remains DISABLED.

Phase B is separately authorized and activates only:
- `padataset-scientific-single-gpu-v1`
- `padataset:scientific-single-gpu`

It requires exact workflow/runtime/data/no-stale-run proof plus exact target scale-set identity with zero assigned/running work.

## Next safe action

Implement and regression-cover the two-phase additive scientific activation transaction and effective-generation verifier support on `padataset-autonomous-scientific-execution-v1`, based on promoted main `dff9024e16f36767facd3cbbbf1009f62b9899f7`.

Do NOT mutate live host state. After implementation, open a fresh PR and require normal validation PASS followed by exactly one authoritative `/workspace-control-validate <frozen-head>` PASS on that identical SHA.

## Remaining gates

- Repository implementation + regression tests for additive effective-generation expansion and target-only activation.
- Normal + authoritative exact-head validation and merge.
- Explicit root/operator authority for live Phase A.
- Exact scale-set/workflow/runtime/data/no-stale-run preflight and explicit root/operator authority for Phase B.
- Scientific smoke → bounded training smoke → full PA2 Stage03 backbone training → Architecture C evaluation.
- Refresh Workspace Shell trusted task authority only after final activation state is durable.

## Safety boundaries

- Existing CPU/GPU/control v3 classes/routes must not be disturbed.
- Historical v2→v3 cutover must not be replayed.
- Separate primary-rate-limit HTTP 403 controller defect remains out of scope.
- Privileged Workspace Shell helpers remain unauthorized for this task until trusted task authority is refreshed after activation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable task:
`tasks/active/padataset-autonomous-scientific-execution-v1.json`

Read the capsule first and follow its `next_safe_action`.
