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

Continue consuming research-engine PR #100 exact-head CI. On PASS, merge PR #100, queue a fresh P3 CPU validation run against unchanged PR #95 head ab36b358a0c7ac33d2887fa681f418033554eae0, then use the newly merged live-output workspace-control launcher to service it with a new short-lived research-engine Administration:write token. Do not rerun PostgreSQL runtime bootstrap; it already passed and remains installed.

## Remaining work

- Consume research-engine PR #100 CI immediately when terminal; merge only on PASS or repair the demonstrated defect.
- After PR #100 merges, queue a fresh /lambda-ci-cpu trigger against unchanged candidate ab36b358a0c7ac33d2887fa681f418033554eae0.
- Use the live-output P3 launcher from workspace-control fbd9a1b9a0f0d811641fd4091c9aed3528b5ab16 or newer exact merged main to launch one cpu-test-v2 JIT runner with a new short-lived PAT.
- Immediately consume the fresh P3 run; continue bounded repair/re-run until install/compile/pytest PASS.
- Only after P3 full PASS begin P4 GPU validation.

## Blockers / gates

- research-engine PR #100 ordinary CI must PASS and merge before a fresh P3 run is armed.
- After PR #100 merges, a fresh P3 run and one short-lived research-engine Administration:write JIT token are required because run 37407910754 is terminal.
- The PAT previously pasted into chat is compromised and must remain revoked; never reuse it.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
