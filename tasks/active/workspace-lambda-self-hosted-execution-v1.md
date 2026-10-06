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

Wait for research-engine PR #98 exact-head ordinary CI. If PASS, merge it, queue a fresh P3 CPU run for PR #95 exact head `ab36b358a0c7ac33d2887fa681f418033554eae0`, then execute the bounded pgvector dependency repair from workspace-control `04b2750bc71818b7ca5be970bda4bc541da4034e` before launching the new P3 JIT runner. Do not advance to P4 until install/compile/full pytest pass on Lambda.

## Remaining work

- Wait for research-engine PR #98 ordinary CI; merge only on PASS.
- Execute workspace-control pgvector repair from exact merged SHA 04b2750bc71818b7ca5be970bda4bc541da4034e and inspect its visible receipt.
- Queue a fresh trusted /lambda-ci-cpu trigger against unchanged PR #95 head ab36b358a0c7ac33d2887fa681f418033554eae0 and launch one new JIT CPU runner.
- Inspect the new P3 receipt/logs; if a new host/candidate incompatibility appears, repair only that demonstrated issue and rerun.
- Only after full P3 PASS, begin P4 bounded GPU validation.

## Blockers / gates

- research-engine PR #98 must pass ordinary CI and merge before the P3 retry is armed.
- The merged pgvector repair must PASS on the real Lambda before a new P3 JIT runner is started.
- The P3 retry must then reach and pass actual candidate install/compile/pytest before P4 may begin.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
