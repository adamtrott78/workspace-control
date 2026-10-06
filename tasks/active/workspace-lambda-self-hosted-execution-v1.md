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

Human-only credential gate: on Lambda create/reuse a clean detached workspace-control tree exactly at `c2c69daa2b61d869dfaad3ff289e4b957201e564` and run `scripts/launch_lambda_ci_p4_gpu.py` under sudo with `WORKSPACE_CI_P4_AUTHORIZED=YES`. The launcher will resolve target UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea to the current NVIDIA minor/device node before creating the systemd unit, grant only that device + /dev/nvidiactl, and pass all other GPU device nodes as explicit denial targets. P4 retry #2 run 37411162940 is already queued on gpu-small-v1. A clean PAT used only in hidden prompts may be reused.

## Remaining work

- Launch P4 retry #2 run 37411162940 using scripts/launch_lambda_ci_p4_gpu.py from exact workspace-control c2c69daa2b61d869dfaad3ff289e4b957201e564.
- Watch live output; immediately consume the always-uploaded P4 PASS/FAIL receipt and launcher receipt when terminal.
- If CUDA demonstrates a requirement for an additional exact NVIDIA support device node (for example UVM), add only that measured node and rerun; do not grant broad NVIDIA wildcards.
- After P4 PASS, begin P5 autonomous controller/provisioner acceptance.
- P6: second-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- Human-only JIT credential gate: launch queued P4 retry #2 run 37411162940 using exact workspace-control c2c69daa2b61d869dfaad3ff289e4b957201e564. A clean PAT that has only ever been entered into the hidden Lambda prompt may be reused.
- P4 retry #2 must pass UUID-resolved selected-device grant, all non-selected GPU device denials, one visible CUDA device with target UUID, real 256 MiB allocation/free, and post-exit process/GPU cleanup before P5.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
