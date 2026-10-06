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

Human-only credential gate: on Lambda create/reuse a clean detached workspace-control tree exactly at `5ad3396a9b959a1932e0ea2973139ac4a3faae04` and run `scripts/launch_lambda_ci_p4_gpu.py` under sudo with `WORKSPACE_CI_P4_AUTHORIZED=YES`. The launcher now resolves target UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea from `/proc/driver/nvidia/gpus/*/information` to the current Device Minor and `/dev/nvidia<minor>`, grants only that node + /dev/nvidiactl, and passes all other GPU nodes as denial targets. Existing P4 retry #2 run 37411162940 remains queued on gpu-small-v1.

## Remaining work

- Launch queued P4 retry #2 run 37411162940 using scripts/launch_lambda_ci_p4_gpu.py from exact workspace-control 5ad3396a9b959a1932e0ea2973139ac4a3faae04.
- Immediately consume the always-uploaded P4 PASS/FAIL receipt and launcher receipt when terminal.
- If CUDA demonstrates a requirement for an additional exact NVIDIA support device node, add only that measured node and rerun; do not grant broad NVIDIA wildcards.
- After P4 PASS, begin P5 autonomous controller/provisioner acceptance.
- P6: second-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- Human-only JIT credential gate: service still-queued P4 retry #2 run 37411162940 using exact workspace-control 5ad3396a9b959a1932e0ea2973139ac4a3faae04. A clean PAT used only in hidden prompts may be reused.
- P4 retry #2 must pass UUID-resolved selected-device grant, explicit non-selected GPU denial, real CUDA context + 256 MiB allocation, and post-exit cleanup before P5.
