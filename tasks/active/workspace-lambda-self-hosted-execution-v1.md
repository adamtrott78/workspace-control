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

## Current stage

research_engine_pilot

## Next safe action

Human-only credential gate: on Lambda create/reuse a clean detached workspace-control tree exactly at `550371aa7afba3de2af5fa6afe360ad4b21f0511` and run `scripts/launch_lambda_ci_p4_gpu.py` under sudo with `WORKSPACE_CI_P4_AUTHORIZED=YES`. The launcher will grant only /dev/nvidiactl, the UUID-resolved selected physical GPU node, and the exact shared CUDA UVM support nodes /dev/nvidia-uvm plus /dev/nvidia-uvm-tools when present. P4 retry #3 run 37412644570 is already queued on gpu-small-v1. A clean PAT used only in hidden prompts may be reused.

## Remaining work

- Launch queued P4 retry #3 run 37412644570 using scripts/launch_lambda_ci_p4_gpu.py from exact workspace-control 550371aa7afba3de2af5fa6afe360ad4b21f0511.
- Immediately consume the always-uploaded P4 PASS/FAIL hardware receipt and launcher receipt when terminal.
- If CUDA still fails, use the receipt's exact failure stage/reason to add only the next measured support requirement; do not broaden physical GPU access.
- After P4 PASS, begin P5 autonomous controller/provisioner acceptance.
- P6: second-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- Human-only JIT credential gate: launch queued P4 retry #3 run 37412644570 using exact workspace-control 550371aa7afba3de2af5fa6afe360ad4b21f0511. A clean PAT used only in hidden prompts may be reused.
- P4 retry #3 must pass CUDA initialization, exactly one visible target UUID, real 256 MiB allocation/free, explicit non-selected GPU denial, and post-exit project/GPU cleanup before P5.
