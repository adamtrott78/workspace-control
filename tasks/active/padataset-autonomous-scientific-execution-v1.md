<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-autonomous-scientific-execution-v1
- Title: PADataset autonomous scientific execution v1
- Status: IN_PROGRESS
- Capsule schema: v2
- Current stage: scientific_activation_validation

## Goal

Make PADataset scientific GPU experiments autonomously executable by ChatGPT through the existing self-hosted Lambda control plane using an exact root-owned DNNs runtime, exact PR-head provenance, read-only project data/cache authority, bounded experiment request schemas, durable artifacts/receipts, and no per-run operator terminal work.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: padataset-autonomous-scientific-execution-v1
- Remote checkpoint: bb6528faf9643ffddf517891eba70f7988267d40
- Remote verified: false

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

On the Lambda host, inspect workspace-ci-v3-controller@workspace-control-control-small-v1.service read-only (LoadState/ActiveState/SubState/MainPID/Result/NRestarts/is-enabled and recent journal) plus the existence/hash of /etc/workspace-ci/v3/controllers/workspace-control-control-small-v1.json. Return the output. Do not restart the unit or submit a duplicate validation yet.

## Remaining work

- Diagnose why exact-head validation #466 / run 43149651861 / job 130955554208 remains queued without runner assignment; use read-only live controller/provisioner evidence first.
- After #466 succeeds (or after a bounded repair followed by a new exact-head validation if #466 is proven irrecoverably orphaned), recheck main and integrate current main into the activation branch with unchanged scientific tree, then exact-head validate the integrated SHA.
- Advance the validated integrated policy to main so Lambda CI Project Reconcile validates it and the live reconcile controller installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.

## Blockers / gates

- Dedicated exact-head Lambda CI Workspace Control Validation #466 / run 43149651861 / job 130955554208 remains queued without runner assignment.
- The initial operator diagnostic checked legacy/v2 workspace-control-cpu controller instances. Those are expected inactive after the committed v3 production cutover and therefore do not explain #466.
- The authoritative runner class for control-validation is workspace-control-control-small-v1 with scale set lambda-workspace-control-control-small and unit workspace-ci-v3-controller@workspace-control-control-small-v1.service. Read-only status/log evidence for that exact unit is required before any restart or retry.
- Scientific route must not be reconciled or invoked until the integrated main-compatible activation head passes exact-head validation and live reconciliation succeeds.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
