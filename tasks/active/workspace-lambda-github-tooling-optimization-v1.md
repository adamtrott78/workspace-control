<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-github-tooling-optimization-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-github-tooling-optimization-v1
- Title: Workspace Lambda GitHub Tooling Optimization v1
- Status: CHECKPOINTED
- Capsule schema: v2
- Parent owner: workspace-lambda-self-hosted-execution-v1

## Goal

Generalize and optimize the reusable workspace-control tooling that connects ChatGPT/GitHub workflows to project-isolated Lambda self-hosted execution, reducing human-terminal mediation and repeated project-specific glue while preserving the accepted security, provenance, exact-SHA, cleanup, and rollback boundaries proven by the current research-engine pilot.

## Exact initialization anchors

- workspace-control main: `bb0b234b79498c14f7e7bdee18a787a69a0c29a8`
- optimization branch: `workspace-lambda-github-tooling-optimization-v1`
- research-engine main observed: `62d91642a1df0ec52b778d8d4a4f3e743382e977`
- authoritative runner task: `tasks/active/workspace-lambda-self-hosted-execution-v1.json`
- P3 retry observed at initialization: run `37396492836` QUEUED
- heartbeat side-project: `tasks/active/workspace-heartbeat-plugin-v1.json`

## Next safe action

CHECKPOINTED. Finish or explicitly suspend Workspace Heartbeat v0.4.0 first. When the user transfers ownership to Lambda/GitHub tooling optimization, start from workspace-control root, rehydrate `tasks/active/workspace-lambda-self-hosted-execution-v1.json` and this child capsule, refresh exact Git heads and current P3/P4/P5 evidence, then perform a duplication/latency/operator-friction inventory before changing shared tooling.

## Remaining work

- After ownership transfers, rehydrate the parent runner task and exact workspace-control/research-engine heads; do not trust the initialization-time queued P3 state if it has advanced.
- Inventory duplicate project-specific launcher/bootstrap/receipt/cleanup logic created during P2/P3/P4/P5 and classify reusable versus project-domain-specific components.
- Define a versioned project execution profile schema for repository/workflow identity, exact SHA, resource class, dependency prerequisites, artifact contract, cleanup, and denied capabilities.
- Consolidate generic GitHub dispatch/JIT runner lifecycle/evidence-consumption logic behind workspace-control procedures/scripts/workflows while preserving repository-specific trusted workflow code where required.
- Measure current end-to-end latency and human-intervention count, then validate improvements against the accepted research-engine pilot.
- Demonstrate a second bounded project/profile without cross-project authority leakage.
- Promote only validated reusable mechanics; leave research-engine scientific/production semantics in research-engine.

## Blockers / gates

- Do not begin broad optimization while heartbeat v0.4.0 is still the explicitly active side-project unless the user transfers ownership.
- Before mutation, rehydrate workspace-lambda-self-hosted-execution-v1 because P3 retry/P4/P5 state can advance independently and is authoritative.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/workspace-lambda-github-tooling-optimization-v1.json`

Start from the normal workspace-control root route.

Treat this capsule as the optimization child of `workspace-lambda-self-hosted-execution-v1`, not as a replacement for the active P3/P4/P5 acceptance task.

Before mutation, rehydrate both task capsules and refresh exact workspace-control/research-engine Git state. Heartbeat v0.4 was intentionally treated as a side project; if it is not closed yet, finish or explicitly suspend it before starting broad Lambda/GitHub optimization.

Do not rely on previous chat prose.


## 2026-10-05 ownership transfer and inventory checkpoint

Heartbeat v0.4.1 is accepted and closed. This child task is now active.

Current refreshed state:

- workspace-control main: `d6f1b02ddd8f611ab99b908123c0e5e5ef59d29a`
- research-engine main: `72e3e16ca118c4756c528392158738a39cb5d5aa`
- parent P3 run `37398604653`: still queued on `cpu-test-v2`
- parent remains at the human-only isolated-runtime bootstrap + one-job JIT gate

Measured duplication:

- `scripts/launch_lambda_ci_p2b_noop.py`: 427 lines
- `scripts/launch_lambda_ci_p3_cpu.py`: 427 lines
- 405 lines match at the same positions (94.8%)
- identical function sets
- only top-level constant difference: timeout 900 vs 2100 seconds
- remaining differences are labels, phase names, authorization env names, runner/unit/job/output names, and receipt text

This strongly supports one generic profile-driven JIT launcher rather than continuing phase-specific copies.

The existing project manifest and systemd profile files already contain most resource/isolation policy. The next design step is to make one versioned execution-profile contract the single source of truth and keep dependency bootstrap project/profile-scoped.
