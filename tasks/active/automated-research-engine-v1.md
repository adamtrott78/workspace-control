<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/automated-research-engine-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: automated-research-engine-v1
- Title: Automated research engine v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design and prove a provenance-preserving automated research engine that turns scholarly literature into structured evidence, durable knowledge, challenged research gaps, fundable research programs, and workspace-control-executable research projects.

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: 2ee1f6584178df68d1f01a219fb526d4745707bf

## Recovery restore point

- Identity: 078cef22ccb68e0538e52654bc9f25ce64aaac5b
- stage=production_daemon_v1
- last_validated_boundary=research-engine/main@078cef22ccb68e0538e52654bc9f25ce64aaac5b; PR #12 24/7 daemon supervisor PASS
- model_backed_acceptance=model credential availability remains unverified from this executor; secret APIs are unavailable and direct secret-probe mutation was blocked before GitHub state changed
- resume=package daemon for persistent Lambda deployment (container/systemd/env templates, restart semantics, artifact volume, database dependency), validate packaging in CI, then continue budget guardrails that do not require model credentials

## Next safe action

From research-engine/main@078cef22ccb68e0538e52654bc9f25ce64aaac5b, add deployment packaging for the 24/7 daemon: container/service definition, persistent artifact volume, PostgreSQL health dependency, restart behavior, and non-secret environment template. Validate in CI, then add budget guardrails. Model-backed acceptance remains a separate credential-gated stage.

## Remaining work

- Package the validated daemon for persistent Lambda deployment with restart-safe service/container configuration, persistent artifact storage, and explicit environment templates.
- Add production budget guardrails around tier concurrency/token usage after the deployment surface is validated.
- Run one real model-backed autonomous research cycle on a model-authenticated runtime and inspect the durable human-review payload.
- After production runtime acceptance, use the autonomous cycle to resume deferred RF corpus expansion instead of manually shepherding papers.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
