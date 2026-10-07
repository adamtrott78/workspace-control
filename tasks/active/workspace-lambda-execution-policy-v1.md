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
- Remote checkpoint: fd9213ab8a7cbd9525ebab78de4f64d03981e4b2
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 9b025b3b1092d1c4e0c1f98678472341d26ee354
- Remote verified: true

## Next safe action

On Lambda, perform a narrow read-only verification for request fa97e66f-c71c-5e48-926a-129a7ecde8b3 after successful GitHub run 37546267761: locate the root P5 runtime receipt/log naturally written for that request, print only its non-secret decision/admission identity/runner/profile/cleanup fields, and prove there is no remaining job directory, staging directory, runner process, or project-UID process for the completed CPU job. Do not add probes or mutate production/scientific state. If cleanup passes, record CPU acceptance and trigger a NEW `/lambda-ci-p5-gpu f5ba8278d7dfa22e63623ddf51896a6dec002813` on research-engine PR #106. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Verify the root runtime receipt and residue-free cleanup for successful CPU run 37546267761; then launch fresh gpu-small admission-v2 acceptance and validate its exact GPU/receipt/cleanup evidence.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- CPU GitHub workflow acceptance passed, but root-owned runtime receipt and residue-free post-run cleanup have not yet been independently verified after run 37546267761. Verify that before gpu-small.
- Do not launch gpu-small until the CPU root receipt binds request fa97e66f-c71c-5e48-926a-129a7ecde8b3 / runner lambda-research-engine-8fb642f3900d and proves runner/job/staging cleanup.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
