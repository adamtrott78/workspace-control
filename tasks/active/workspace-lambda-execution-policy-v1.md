<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-execution-policy-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-execution-policy-v1
- Title: Workspace Lambda Execution Policy and Model Workload Governance v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, implement, and adversarially validate a fail-closed workload admission, trusted model/dependency cache, resource-governance, and execution-evidence layer on top of the accepted Lambda P5 CPU and gpu-small autonomous runner substrate so ChatGPT/GitHub-driven work can safely execute pinned model-scale workloads without granting candidate workflow code the ability to invent capabilities, persist mutable cross-job state, access production/scientific state, or widen host authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d43ad9a27ad5c4769f63519787612c3f549be13d
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8a74d1f0061a687b7a7e30bbd9f846919424b79e
- Remote verified: true

## Next safe action

Reinstall exact workspace-control implementation d43ad9a27ad5c4769f63519787612c3f549be13d on Lambda using the existing authorized P5 bootstrap. Require corrected bootstrap blob fbd33b8d73c8a6e94dbe13b29e656e26973c814b and installed trusted-cache manager content blob a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807 with stat root:root regular file mode 555 before promoted-model verification. Then rerun the host installation/identity gate: verify exact admission 19e10ded65eea4924673bf7a9efa3c7f27767c4d, provisioner f8a0e1ddd6a770d46cb6c2fb017f58e3baa86260, provisioner-service 74e7838e44eebd3a73dde620a61d3b052d78e466, runtime e09aa9d6961615a259c825d436f95adce668441f, project manifest b41bba55dd8f5fcef594b00289e14c2409a2e081, workload policy 5e44397963dbe660600d0e8dab9645d5d13d456f, promoted Qwen object 6e28e2560c07e7dabab92c55dbfb6941d5a7a75c8068bdc7a98115d8dc62072c / descriptor b6182b15ff0549d9b3b1d3780fdb655c6df7653ad7ec3a5d72336b5571b3fe74 / revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a, expanded runtime tree b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63, active provisioner/CPU/GPU controllers, and zero project/GPU residue. Do not trigger /lambda-ci-qwen35-pilot or load/infer Qwen until this corrected identity gate passes.

## Remaining work

- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small under the already-promoted model/runtime identities.
- Decide separately whether gpu-heavy or dual-GPU should ever be accepted; they remain denied.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
