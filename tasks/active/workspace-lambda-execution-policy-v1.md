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
- Remote checkpoint: effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: fa0ff6f1a4a46fd0295e45df401aa8361d220c86
- Remote verified: true

## Next safe action

Run one bounded root-authored disposable trusted-cache integrity canary using the exact installed manager blob a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807. Use only temporary state/trusted roots under the operator-visible workspace-control-tmp directory and a fresh test-fixture descriptor/source. First acquire/promote/verify the untouched disposable object PASS. Then make independent writable copies of that disposable promoted object and prove fail-closed verification for: (1) payload content tamper, (2) receipt descriptor/descriptor-digest inconsistency, and (3) incomplete snapshot by removing one payload file. Confirm the untouched disposable original still verifies PASS/read_only=true/offline_complete=true afterward, temporary quarantine is destroyed, no real /var/lib/workspace-ci/cache-manager or /srv/workspace-ci/research-engine/trusted-cache object is modified, no candidate payload or GitHub job runs, and no model weights/inference occur. After PASS, checkpoint adversarial_recovery_and_resource_validation as VALIDATED and proceed to the first offline pinned Qwen3.5-4B gpu-small model pilot.

## Remaining work

- Run cache poisoning and incomplete-snapshot rejection acceptance against the trusted-cache boundary.
- After the adversarial recovery/resource/cache matrix is complete, run the first offline Qwen3.5-4B pinned-model pilot on gpu-small under the already-promoted model/runtime identities.
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
