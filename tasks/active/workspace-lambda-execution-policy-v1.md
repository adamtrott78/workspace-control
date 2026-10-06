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
- Remote checkpoint: 10901ebef59983da2d499ebd57125667c21edddf
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 12dd0f2f9510f682f0b62fe8fdc9a63494da8d6d
- Remote verified: true

## Next safe action

On Lambda from the normal operator account, install and activate exact corrected workspace-control 10901ebef59983da2d499ebd57125667c21edddf using a fresh detached worktree inside an explicit child bash so failures return to the existing SSH prompt. Verify exact clean HEAD, then invoke the canonical scripts/bootstrap_lambda_ci_p5.sh via sudo with WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES, WORKSPACE_CI_P5_EXPECTED_SHA=10901ebef59983da2d499ebd57125667c21edddf, and WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES. Do not restage the already-valid controller credential. Require the install receipt to show both controllers ACTIVE, provisioner active, controller_credential_ready=true, and production_services_modified=false. After that PASS, create a NEW trusted /lambda-ci-p5 <exact_sha> issue-comment run on the open same-repository non-scientific research-engine candidate (or an equivalent fresh candidate) and require it to complete; do not count pre-fix queued run 37533291290 as sole acceptance evidence. Then trigger a fresh /lambda-ci-p5-gpu <exact_sha> run and validate both root receipts and residue-free cleanup. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Install and activate corrected workspace-control 10901ebef59983da2d499ebd57125667c21edddf on Lambda, then run fresh non-scientific admission-v2 CPU and gpu-small acceptance and validate root receipts plus residue-free cleanup.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Lambda host still runs the earlier d2326042 admission-v2 controller. Exact corrected workspace-control 10901ebef59983da2d499ebd57125667c21edddf must be installed and activated through the reviewed sudo bootstrap before fresh CPU/GPU acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
