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

## Recovery restore point

- Identity: 078cef22ccb68e0538e52654bc9f25ce64aaac5b
- stage=production_daemon_v1
- last_validated_boundary=research-engine/main@078cef22ccb68e0538e52654bc9f25ce64aaac5b; PR #12 supervisor core PASS
- in_flight=research-engine PR #13 head daemon-deployment-v1@fea82bf51148f8278e0a3243b46174f3504ed3ff
- slice=daemon deployment packaging: Docker image, Compose PostgreSQL dependency + persistent artifact volume + restart policy, user systemd template, env template, CI compose validation/image build
- resume=inspect PR #13 CI; repair packaging remotely if failing; merge if green; then continue budget guardrails

## Next safe action

Inspect research-engine PR #13 for daemon-deployment-v1@fea82bf51148f8278e0a3243b46174f3504ed3ff. Repair CI remotely if failing; merge if green. Then continue production budget guardrails while model-backed acceptance remains credential-gated.

## Remaining work

- Package the validated daemon for persistent Lambda deployment with restart-safe service/container configuration, persistent artifact storage, and explicit environment templates.
- Add production budget guardrails around tier concurrency/token usage after the deployment surface is validated.
- Run one real model-backed autonomous research cycle on a model-authenticated runtime and inspect the durable human-review payload.
- After production runtime acceptance, use the autonomous cycle to resume deferred RF corpus expansion instead of manually shepherding papers.

## Blockers / gates

- None.