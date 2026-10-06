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

## Parent execution owner

research-engine-local-extract-redesign-v1

## Current stage

research_engine_pilot

## Next safe action

Human-only credential gate: on Lambda create/reuse a clean detached workspace-control tree exactly at `12a735c7fea085dc3221588245657c67ae048f7f` and run `scripts/launch_lambda_ci_p4_gpu.py` under sudo with `WORKSPACE_CI_P4_AUTHORIZED=YES`. Paste a newly-created short-lived fine-grained GitHub PAT scoped only to `adamtrott78/research-engine` with repository Administration:write into the hidden prompt. The launcher streams output live. Fresh P4 run 37410285336 is already queued on gpu-small-v1. Do not rebuild PostgreSQL or start model/scientific work.

## Remaining work

- Launch queued P4 run 37410285336 using scripts/launch_lambda_ci_p4_gpu.py from exact workspace-control 12a735c7fea085dc3221588245657c67ae048f7f.
- Watch live runner output; immediately consume the GitHub P4 artifact and launcher receipt when terminal.
- If a measured additional NVIDIA device node is required for basic CUDA Driver API allocation, add only that exact device and rerun; never grant GPU1 or broad NVIDIA wildcards without evidence.
- After P4 PASS, begin P5 autonomous scale-set listener + narrow root provisioner acceptance so routine jobs no longer require human PAT/SSH relay.
- P6: second-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- Human-only JIT credential gate: launch P4 run 37410285336 with workspace-control 12a735c7fea085dc3221588245657c67ae048f7f and a newly-created short-lived research-engine Administration:write token pasted only into the hidden prompt.
- P4 must return PASS for GPU0-only device boundary, real CUDA allocation, GPU1 denial, and post-exit project/GPU process cleanup before P5.
- Any PAT previously pasted into chat is compromised and must remain revoked.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
