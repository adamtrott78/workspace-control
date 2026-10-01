# Workspace Control Task Handoff

Authoritative capsule: tasks/active/automated-research-engine-v1.json

## Recovery restore point

- Identity: c29e41d812f2e5a3b492649b2d4538662cd8012d
- stage=production_daemon_v1
- last_validated_boundary=research-engine/main@c29e41d812f2e5a3b492649b2d4538662cd8012d; PR #13 deployment packaging PASS
- resume=add durable model-usage ledger and per-run budget enforcement/pause-resume semantics; validate in PostgreSQL CI; model-backed acceptance remains credential-gated

## Next safe action

From research-engine/main@c29e41d812f2e5a3b492649b2d4538662cd8012d, add durable semantic usage accounting and per-run budget guardrails. Prevent PAUSED_BUDGET runs from leasing new jobs, expose budget state in health/overnight reports, and require explicit resume after policy change. Validate in PostgreSQL CI.

## Remaining work

- Package the validated daemon for persistent Lambda deployment with restart-safe service/container configuration, persistent artifact storage, and explicit environment templates.
- Add production budget guardrails around tier concurrency/token usage after the deployment surface is validated.
- Run one real model-backed autonomous research cycle on a model-authenticated runtime and inspect the durable human-review payload.
- After production runtime acceptance, use the autonomous cycle to resume deferred RF corpus expansion instead of manually shepherding papers.

## Blockers / gates

- None.