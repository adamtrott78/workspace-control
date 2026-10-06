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
- Remote checkpoint: 526e020a4d4ef429ceeac173b9f51fbd75912d99
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 12dd0f2f9510f682f0b62fe8fdc9a63494da8d6d
- Remote verified: true

## Next safe action

First cancel stale research-engine CPU workflow runs 37533291290 and 37534646664 in GitHub Actions so no pre-fix assigned job remains eligible to consume a newly admitted runner. Then, on Lambda from the normal operator account, install and activate exact corrected workspace-control 526e020a4d4ef429ceeac173b9f51fbd75912d99 using a fresh detached worktree inside an explicit child bash. Verify exact clean HEAD and invoke scripts/bootstrap_lambda_ci_p5.sh via sudo with WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES, WORKSPACE_CI_P5_EXPECTED_SHA=526e020a4d4ef429ceeac173b9f51fbd75912d99, and WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES. Do not restage the valid controller credential. Require both controllers ACTIVE, provisioner active, credential ready, production services unchanged, and CPU controller restart count stable after activation. Only then trigger a NEW /lambda-ci-p5 <exact_sha> run on the open non-scientific research-engine candidate; require it to complete before triggering fresh /lambda-ci-p5-gpu <exact_sha>. Do not count runs 37533291290 or 37534646664 as acceptance evidence and do not enable model-scale classes or gpu-heavy.

## Remaining work

- Install and activate corrected workspace-control 526e020a4d4ef429ceeac173b9f51fbd75912d99 on Lambda, cancel stale CPU runs 37533291290 and 37534646664, then run fresh non-scientific admission-v2 CPU and gpu-small acceptance and validate root receipts plus residue-free cleanup.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Lambda host still runs 10901ebef59983da2d499ebd57125667c21edddf and its CPU controller crash-loops on sparse JobAssigned recovery metadata. Exact corrected workspace-control 526e020a4d4ef429ceeac173b9f51fbd75912d99 must be installed and activated before acceptance resumes.
- Stale CPU workflow runs 37533291290 and 37534646664 must be canceled before the next acceptance trigger so no old assigned job can consume a runner admitted for a fresh attestation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
