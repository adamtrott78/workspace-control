<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-self-hosted-execution-v1
- Title: Workspace Lambda Self-Hosted Execution v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, validate, and if safety gates pass pilot a project-isolated GitHub Actions execution lane on the existing Lambda workstation so ChatGPT/GitHub-driven software work can execute and validate directly in the real target environment without routine human-terminal mediation, while preserving project authority, minimizing host risk, and keeping existing GitHub-hosted CI as the known-good control.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: ebfbae64dc82afaf81123ba49b03d170a0196757
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 577764f4db10e4f4f894b1613518c358c6da7b95
- Remote verified: true

## Next safe action

Treat workspace-control ebfbae64dc82afaf81123ba49b03d170a0196757 and research-engine 577764f4db10e4f4f894b1613518c358c6da7b95 as the accepted autonomous CPU+gpu-small baseline. Before enabling gpu-heavy, dual-GPU, model-server, persistent model downloads, production/scientific-state access, or arbitrary model execution, design and validate a P5 execution-policy/model-workload governance contract. Reuse the existing trusted-cache split (candidate-writable staging vs runner-read-only trusted cache) and require immutable model/dependency identity, explicit resource/network/secrets/state-effects declarations, fail-closed admission, and durable execution/cleanup receipts. Then implement the policy in the root-owned project/profile manifests and trusted default-branch workflows, followed by adversarial recovery/cache/resource tests.

## Remaining work

- P5 execution-policy/model-workload governance: define workload classes, admission manifests, model/dependency provenance, trusted-cache promotion, egress/secrets policy, resource profiles, evidence requirements, and explicit forbidden/exception paths before model-scale or gpu-heavy workloads.
- P5 recovery/adversarial acceptance: prove controller restart/recovery, replay protection, cleanup-failure blocking, kill switch behavior, timeout/OOM/disk-pressure handling, and CPU/GPU contention behavior.
- P5 trusted-cache/resource hardening: exercise immutable cache promotion/invalidation, commit-pinned model snapshots, package/model cache poisoning resistance, and bounded failure cleanup.
- P6 second-project isolation pilot: opt in a second repository under a distinct UID/root/cache policy and prove mutual denial.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
