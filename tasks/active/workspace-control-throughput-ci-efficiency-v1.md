<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-control-throughput-ci-efficiency-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-control-throughput-ci-efficiency-v1
- Title: Workspace Control Throughput & CI Efficiency v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Measure and remove avoidable latency from ChatGPT/GitHub/workspace-control execution loops while preserving provenance, fail-closed mutation semantics, durable recovery, and implementation quality. Optimize both orchestration overhead and CI topology so routine low-risk changes do not pay the same synchronous validation cost as high-risk production changes, without weakening the full safety net.

## Current stage

baseline_measurement

## Baseline already captured

- Five recent successful PR CI runs: 73, 75, 81, 81, 91 seconds; mean 80.2 s.
- Five corresponding canonical-main CI runs: 75, 65, 81, 82, 81 seconds; mean 76.8 s.
- Ten runs across five narrow fix cycles: 785 seconds (~13.1 minutes) of CI wall time before assistant polling/tool overhead.
- Observed additional latency sources: serial file-level Git mutations, PRs opened before all follow-up changes were complete, repeated short-interval CI polling, full install/test/PostgreSQL/Compose/Docker-image validation for narrow harness changes, and synchronous waiting for both PR and post-merge CI.

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and follow the normal root route.

Read this capsule plus the task-capsule/operator-workflow contracts. Do not mutate CI yet.

First complete `baseline_measurement`: inspect recent research-engine workflow definitions and representative run/job timing, inventory GitHub connector capabilities that could reduce serial mutations/polling, and produce a measured latency decomposition distinguishing assistant orchestration overhead from actual CI execution.

Then perform source-backed `external_practice_research` before proposing the risk-tiered validation architecture.

## Remaining work

- Measure recent end-to-end control cycles more precisely, including Git mutation counts, PR creation timing, CI restarts, polling calls, and synchronous post-merge waits.
- Inspect the available GitHub connector functions for atomic/multi-file commit and more efficient check-suite/status operations.
- Research authoritative CI/CD and large-repository practices relevant to path-aware testing, affected-test selection, caching, concurrency cancellation, merge/tested-tree semantics, required versus advisory checks, and scheduled full regression.
- Design a risk-tiered validation policy for workspace-control and representative repositories, with explicit escalation conditions and a force-full-validation escape hatch.
- Design an assistant orchestration policy covering mutation batching, PR timing, CI polling cadence, useful parallel work, and when canonical-main CI is or is not on the critical path.
- Implement the smallest safe changes in workspace-control first; only then consider representative research-engine CI changes if measurements justify them.
- Benchmark trivial, moderate, and high-risk control cycles before/after and document both latency and validation coverage.

## Important constraints

- Do not optimize by deleting tests or weakening provenance/safety invariants.
- Do not assume duplicate-looking PR/main CI is redundant without proving tested-tree/merge semantics.
- Keep research-engine read-only during initial measurement/research/design.
- Prefer direct GitHub tooling over unnecessary human shell steps.
- Preserve a force-full-validation path for ambiguous/high-risk changes.
- Every fresh-chat initialization for this task must include the full repository URL below.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/workspace-control-throughput-ci-efficiency-v1.json`

Start from the normal workspace-control root route.

Treat the authoritative task capsule, synchronized Markdown handoff, exact durable Git state, and referenced research-engine CI evidence as the complete handoff.

Do not rely on previous conversation state.

Follow the capsule's exact `next_safe_action`.

Important initial boundary: do **not** begin by changing CI. First measure the actual control-cycle latency and separate assistant orchestration overhead from GitHub Actions runtime, then research documented CI/control-plane practices and design a risk-tiered validation model that preserves full-quality validation for high-consequence changes.
