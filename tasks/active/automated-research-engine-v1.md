<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: tasks/active/automated-research-engine-v1.json

## Task

- ID: automated-research-engine-v1
- Status: IN_PROGRESS
- Current stage: agentic_orchestration_v1

## Recovery restore point

- Identity: 80ca8cdc6d35d8c8c8b6099f8cf370de41d18ee2
- stage=agentic_orchestration_v1
- last_validated_boundary=research-engine/main@80ca8cdc6d35d8c8c8b6099f8cf370de41d18ee2; PR #7 autonomous PostgreSQL cycle PASS
- resume=implement production Responses API executor behind JobExecutor: configurable CHEAP/STANDARD/STRONG model profiles, structured JSON results, refusal/incomplete handling, usage metadata, and tests with mocked client; keep DETERMINISTIC and HUMAN outside model executor

## Next safe action

Branch from research-engine/main@80ca8cdc6d35d8c8c8b6099f8cf370de41d18ee2 and implement the production OpenAI Responses semantic executor behind the existing JobExecutor interface. Map CHEAP/STANDARD/STRONG through configurable model profiles, require structured JSON output, persist model/usage metadata, handle refusals/incomplete responses as retryable/non-retryable failures, and validate with mocked API tests before wiring a real credentialed worker runtime.
