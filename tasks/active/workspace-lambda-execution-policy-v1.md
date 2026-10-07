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
- Remote checkpoint: 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 66361693ad2f8d0a345d420dabccbbd6042f5c59
- Remote verified: true

## Next safe action

On Lambda, perform a read-only structural and identity classification of ~/.research-engine/residual-runtimes/qwen3.5-4b-vllm-0.30.0 before any runtime acquisition. Record regular-file, symlink, directory, special-entry, and materialized-byte counts; enumerate every symlink target without following it; read and validate .workspace-control-ready.json against runtime contract qwen35-vllm-cu129-image-native-sampler-v3; verify vLLM distribution 0.30.0+cu129 and direct_url wheel SHA-256 e98cb69659bfcfc849cf11ce0781a7161d40b02b51a6c3636924a5909f2aabcc, torch 2.13.0+cu129 with CUDA 12.9, torchvision 0.28.0+cu129, torchcodec 0.16.0+cu129, and VLLM_USE_FLASHINFER_SAMPLER=0 semantics from owning evidence. Capture the current sorted pip freeze and identify whether the environment contains absolute-path shebangs, symlinks, or other relocation hazards. Because trusted-cache v1 forbids symlinks, do not call acquire-local on the raw venv unless the observed tree is policy-compatible. Do not rebuild/download packages, run model inference, stop/start the production daemon, mutate scientific state, or alter the accepted model object. Use the classification to choose the smallest exact runtime/dependency representation that can be promoted read-only and consumed offline on gpu-small.

## Remaining work

- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- The exact Qwen model object is accepted. The next unresolved boundary is runtime packaging: the existing qwen35-vllm-cu129-image-native-sampler-v3 environment is a Python venv, while trusted-cache v1 rejects symlinks and non-regular payload entries. Observe the existing runtime tree and exact package identity before choosing a promotable, read-only offline representation; do not blindly promote the raw venv.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
