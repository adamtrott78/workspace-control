<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-semantic-execution-migration-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-semantic-execution-migration-v1
- Title: Workspace Semantic Execution Migration v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, benchmark, and incrementally migrate Workspace Control to an open-world semantic execution architecture that preserves current research, engineering, tutoring, publication, presentation, document, data-science, and operations workflows while minimizing scarce frontier-model allowance through deterministic execution, resumable Instant/local reasoning, bounded context, capability-aware routing, and explicit escalation—without weakening project-local truth, provenance, authority, GitRunner/Workspace Shell security, or rollback.

## Workflow

- Repository: workspace-control
- Path: workflows/evidence-first-solution-research.v1.json
- Checkpoint: d47a7922aa8d47d3a22b55c19ce4d6af7309a964

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-semantic-execution-migration-v1
- Remote checkpoint: 54ccc5c2e45841ba1e0ee22eed074f24a022712c
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: main
- Remote checkpoint: a8f952c7cf964730a01b2dc5c6cd75850912f94f
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 1031861c03b2af8cff5cf72939bbbc83a95e65a4
- Remote verified: true

### MTH602-AdamTrott

- Intent: read
- Remote branch: hw3-exam1-prep
- Remote checkpoint: 747e49fb9219b949e0b0e9d15860a766fbcb1f23
- Remote verified: true

### EAS501-AdamTrott

- Intent: read
- Remote branch: eas501-tutor-bootstrap
- Remote checkpoint: b2b390d042d539165f140821a3080dc4e5a82001
- Remote verified: true

### CIS560-AdamTrott

- Intent: read
- Remote branch: tutor-framework
- Remote checkpoint: aba8c2e87dd4bb50ba414206270f592e8ca841a4
- Remote verified: true

## Next safe action

E3-A9 ROOT-CANDIDATE INTAKE DIAGNOSTIC / REPAIR. E3-A8 authority 0f8d98af4c7ac83e3b78fe2a59e9bc13f1b6fa28 is CONSUMED FAIL and non-reusable. Closeout is frozen at 884995786caacced63098f5a592895ae328cd2cc. The root candidate commit 968db0800e9dcdee6e5a784889d74653276fb184 is a single append-only child of baseline fedc3277b12f83e7e5e2cbdb8ca6b19205ba4f2f and its JSON matches the frozen worker-result schema shape, but final durable state still had worker_results=0, root RUNNING@0, session BOUND@0 and action AWAITING_DURABLE_ACK with sent_unconfirmed=1. No new live authority exists. First reproduce the exact root packet/candidate deterministically, assert packet SHA f104a451c60ee168f9236b0075b1a00c20b2bb12f40dbd23b414dff6ae74d60b, replay commit 968db080… through the immutable candidate/intake path, and capture the exact exception or PASS before changing runtime code or proposing another live attempt.

## Remaining work

- E3-A9: deterministically reproduce the exact root token 63e9b17e492c4ed3a36d20c83172abf3, compile the root packet and assert packet SHA f104a451c60ee168f9236b0075b1a00c20b2bb12f40dbd23b414dff6ae74d60b; replay exact raw candidate commit 968db0800e9dcdee6e5a784889d74653276fb184 against an equivalent AWAITING_DURABLE_ACK root action/session/process and record the exact intake outcome.
- E3-A9: if deterministic replay fails, repair only the proven binding/intake defect and add regression coverage; if it passes, instrument CandidateWatcher/intake to emit a compact exact exception marker before the large resource report. Also make worker-result schema provenance explicit from the validated source/review head rather than guessing candidate-branch location.
- E3-A9 REVIEW: validate the repair head and freeze a new zero-authority review. Do not create any live authority until that review is green and Adam gives a fresh explicit approval.
- E4: run calibrated economics comparison versus all-strong/frontier control only when comparable allowance telemetry is available.
- E5: run authoritative target-machine UX-09 performance benchmark.
- E6: mechanically audit exact SHA/blob/route provenance, authority boundaries, rollback paths and unresolved violations.
- E7: reconcile every November acceptance-matrix requirement to PASS or explicit promotion blocker.
- E8: record explicit integrated PROMOTE_V0 / HOLD / REVISE verdict.

## Blockers / gates

- E3-A9 ROOT INTAKE DIAGNOSTIC: the exact execution_error field was not present in the captured terminal tail. Durable evidence proves the candidate was not registered (worker_results=0) and the root action remained AWAITING_DURABLE_ACK; deterministic replay is required before any repair claim.
- E3 LIVE AUTHORITY: none exists. A8 authority 0f8d98af4c7ac83e3b78fe2a59e9bc13f1b6fa28 is consumed and non-reusable; no silent retry is permitted.
- E4 ECONOMICS: claim-bearing comparison remains gated on calibrated comparable allowance telemetry; do not substitute raw token estimates or uncalibrated UI observations.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
