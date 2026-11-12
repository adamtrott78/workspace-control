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

First recover Workspace Heartbeat separately by diagnosing exact v0.4.8 local MCP startup (runtime SHA, node_modules, port 8787 ownership, and an isolated ephemeral-port Node startup). For validation #466, perform one fresh authenticated rate-limit probe after reset; if remaining quota is positive, start workspace-ci-v3-controller@workspace-control-control-small-v1.service and verify it remains active before rechecking #466. Do not cancel or duplicate #466.

## Remaining work

- Contain the v3 control-small controller restart storm and recover after the GitHub REST primary-rate-limit window resets; preserve validation #466 without duplicate requests.
- Once #466 runs, require SUCCESS or diagnose its exact failure. Then recheck main and integrate current main into the activation branch with unchanged scientific tree, followed by exact-head validation of the integrated SHA.
- Advance the validated integrated policy to main so Lambda CI Project Reconcile installs the exact runtime/data/contract/route policy.
- Verify live reconciliation and run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.
- Track the v3 controller 403 rate-limit handling defect for a separately authorized infrastructure hotfix; current code retries 429/5xx but treats primary-rate-limit 403 as fatal.

## Blockers / gates

- Dedicated exact-head Lambda CI Workspace Control Validation #466 / run 43149651861 / job 130955554208 remains queued without runner assignment.
- Root cause is proven: workspace-ci-v3-controller@workspace-control-control-small-v1.service restart-stormed on GitHub primary-rate-limit HTTP 403 while discovering REST-attested queued demand.
- The exact v3 control-small controller is intentionally stopped/inactive at NRestarts=3495, containing further rate-limit amplification.
- Authenticated secret-safe probe at 2026-11-12 07:55:11 EST returned core quota 0/5000, used=5002, reset epoch 1794488297 = 2026-11-12 07:58:17 EST. A fresh post-reset probe is required before restarting.
- Workspace Heartbeat is independently unavailable after operator heartbeat-down/heartbeat-up: launcher reports v0.4.8 MCP server failed to become healthy before tunnel startup. This is a separate operator infrastructure incident and does not change validation #466 authority.
- Scientific route must not be reconciled or invoked until exact-head validation and live reconciliation succeed.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
