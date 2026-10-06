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

On Lambda, use one clean detached workspace-control tree exactly at `04b2750bc71818b7ca5be970bda4bc541da4034e`. First run `scripts/bootstrap_lambda_ci_p3_pgvector.sh` under sudo with `WORKSPACE_CI_P3_PGVECTOR_AUTHORIZED=YES` and `WORKSPACE_CI_P3_PGVECTOR_EXPECTED_SHA=04b2750bc71818b7ca5be970bda4bc541da4034e`. If and only if it reports PASS, run `scripts/launch_lambda_ci_p3_cpu.py` under sudo with `WORKSPACE_CI_P3_AUTHORIZED=YES` and paste a short-lived research-engine Administration:write token only into its hidden prompt. The trusted P3 retry is already queued as run 37396492836 against unchanged candidate ab36b358a0c7ac33d2887fa681f418033554eae0. Return the pgvector receipt and P3 launcher receipt, or compact failure output if the repair fails.

## Remaining work

- Execute workspace-control pgvector repair from exact SHA 04b2750bc71818b7ca5be970bda4bc541da4034e; require its smoke test and production-master invariants to PASS.
- Only after repair PASS, execute the P3 one-job JIT launcher from the same detached tree and service queued run 37396492836.
- Inspect the new GitHub receipt/logs and local launcher receipt; repair only any newly demonstrated host/candidate issue.
- Only after P3 full PASS, begin P4 bounded GPU validation.

## Blockers / gates

- The bounded pgvector dependency bootstrap must PASS on real Lambda before P3 retry #2 runner launch.
- P3 retry #2 must reach and pass candidate install/compile/full pytest before P4 may begin.
- Until P5 autonomous controller acceptance, the JIT runner still requires a short-lived local research-engine Administration:write token prompt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
