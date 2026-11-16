<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Extend the live Workspace Shell v1 lineage with first-class PADataset access and a permanent candidate-evidence path that can validate exact candidate SHAs without promoting them to durable task authority, while preserving credential isolation, private-repository support, rollback, and exact-SHA authoritative execution.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-candidate-evidence-current-v1
- Remote checkpoint: d02bfd36ed06457698a3f1e120d9a84e2349cf5f
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

After this JSON+Markdown control-cycle state passes exact-head validation, retry the transactional root activation using the exact authority-state commit, Workspace Shell runtime d02bfd36ed06457698a3f1e120d9a84e2349cf5f (#2928 SUCCESS), PADataset execution befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule source 8019248f6952743d61e90d5abac754356952c18b, and semantic execution binding 7c20097c5f177f23c16a765b95ce94d7161f0d29. Require SEMANTIC_DURABLE_TASK_BINDING=PASS, LOCAL_SEMANTIC_TASK_MCP=PASS, LOCAL_SEMANTIC_TASK_RECEIPT=PASS, EVALUATOR_SEALED_ROOT=PASS, LOCAL_EVALUATOR_CONTROL_READBACK=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_MCP=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Roll back on any failure. Do not widen any other profile, generic shell/interpreter, root/sudo, helper/issuer, network, evaluator path, PADataset, or GPU authority. After PASS, independently verify semantic HEAD 7c20097c… and proceed to the frozen fake-worker private-route harness.

## Remaining work

- Retry the rollback-capable root activation from the exact authority-state commit produced by this control cycle using Workspace Shell runtime d02bfd36ed06457698a3f1e120d9a84e2349cf5f, PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule 8019248f6952743d61e90d5abac754356952c18b, and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29.
- Require SEMANTIC_DURABLE_TASK_BINDING=PASS, LOCAL_SEMANTIC_TASK_MCP=PASS, LOCAL_SEMANTIC_TASK_RECEIPT=PASS, EVALUATOR_SEALED_ROOT=PASS, LOCAL_EVALUATOR_CONTROL_READBACK=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_MCP=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS; rollback remains mandatory on any failure.
- After activation PASS, independently verify live Workspace Shell runtime d02bfd36… and semantic execution 7c20097c…, then run the frozen fake-worker private-route harness.

## Blockers / gates

- Repaired runtime d02bfd36ed06457698a3f1e120d9a84e2349cf5f is repository-validated but not live. The fifth activation remains rolled back.
- The fifth retry passed semantic/evaluator MCP calls and local task authority. The only observed failure was that raw MCP structured output did not include a schema-declared receipt_id.
- Runtime d02bfd36… explicitly exposes the already-generated opaque receipt_id in workspace_shell_exec structured output while preserving the launcher, exact receipt validation, and all execution authority boundaries.
- Live activation remains an operator/root gate. Success still requires semantic task receipt PASS, evaluator worker-denial receipt PASS, evaluator isolation acceptance PASS, and full transactional upgrade PASS with rollback on any failure.
- Existing helper, issuer, generic shell/interpreter, network, evaluator-path, PADataset, GPU, and privileged authority boundaries remain unchanged.
- After activation succeeds, independently verify live semantic task exact HEAD 7c20097c5f177f23c16a765b95ce94d7161f0d29 before the frozen fake-worker private-route harness.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
