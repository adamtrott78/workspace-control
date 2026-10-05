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

safe_runner_foundation

## Next safe action

On Lambda, create a clean detached workspace-control worktree exactly at `fb86b027c096af9f92f949050564799ce87f2052`, then execute `scripts/launch_lambda_ci_p2b_noop.py` from that detached tree with `WORKSPACE_CI_P2B_AUTHORIZED=YES` under sudo. When prompted, paste a short-lived fine-grained GitHub PAT scoped only to `adamtrott78/research-engine` with repository Administration:write. Do not put the token in the command, chat, Git, or a file. The trusted GitHub run is already queued as run 37383893507; after launcher exit, return only the non-secret local `lambda-ci-p2b-launcher.json` receipt.

## Remaining work

- Create a short-lived fine-grained GitHub PAT scoped only to research-engine with repository Administration: Read and write; paste it only into the local launcher prompt.
- Execute the reviewed workspace-control P2-B launcher once; it will generate one JIT runner, service queued run 37383893507, then destroy its workspace/config.
- Inspect GitHub run 37383893507 and download/validate lambda-ci-p2b-receipt; compare with local launcher receipt and diagnostics.
- If P2-B passes, close P2 and start P3 CPU candidate validation with candidate checkout, ephemeral environment/database, and artifact return.
- P4: bounded GPU validation with explicit device grant and post-job GPU/process cleanup.
- P5: closed-loop ChatGPT fail-diagnose-fix-rerun-PASS acceptance without SSH.
- P6: second-project cross-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- P2-B requires one local fine-grained GitHub token scoped only to adamtrott78/research-engine with repository Administration:write so the launcher can call the JIT-config endpoint. The token must be pasted only into the Lambda TTY prompt, never into ChatGPT/Git or a shell command.
- P2 completion requires queued run 37383893507 to execute on the JIT runner, return a PASS artifact, and the launcher to prove workspace/project-process cleanup.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
