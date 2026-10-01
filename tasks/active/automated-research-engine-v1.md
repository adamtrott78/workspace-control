<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: tasks/active/automated-research-engine-v1.json

## Task

- ID: automated-research-engine-v1
- Status: IN_PROGRESS
- Current stage: agentic_orchestration_v1

## Recovery restore point

- Identity: 9698089965e7ed015e468e7e5f27453a791e760e
- stage=agentic_orchestration_v1
- last_validated_boundary=research-engine/main@9698089965e7ed015e468e7e5f27453a791e760e; PR #10 authoritative semantic pipeline PASS
- resume=add live web_search only to DISCOVERY/NOVELTY_SEARCH with captured search provenance, add autonomous controller CLI that drives mixed workers to WAITING_HUMAN, then validate final production-shaped v1 through PostgreSQL CI

## Next safe action

From research-engine/main@9698089965e7ed015e468e7e5f27453a791e760e, add live Responses web_search only for DISCOVERY and NOVELTY_SEARCH with durable execution/source provenance, plus an autonomous controller CLI that starts/drives mixed deterministic+semantic workers to WAITING_HUMAN. Validate with PostgreSQL CI; then perform the first production-shaped autonomous research run when a model-authenticated runtime is available.

## Remaining work

- Enable live scholarly/web discovery for DISCOVERY and NOVELTY_SEARCH only; persist search query/source provenance in semantic execution metadata.
- Add a production-shaped autonomous controller command that starts a run, drives heterogeneous workers, recovers expired leases, and stops at WAITING_HUMAN/FAILED/COMPLETED.
- Validate the controller against real PostgreSQL with scripted semantic delegates and production deterministic materialization.
- Run one real model-backed autonomous research cycle on a model-authenticated runtime and inspect the human-review payload.
- Then harden 24/7 Lambda deployment: daemon supervision, concurrency/budgets/backpressure, and overnight reporting.

## Blockers / gates

- None.