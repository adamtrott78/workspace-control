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
- Remote checkpoint: fbb065a235ef271f3c55210833ee3b95e9d61f54
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
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

TEMPORARY P0 INFRASTRUCTURE GATE: allow the separate GitRunner task workspace-github-actions-control-plane-protocol-redesign-v1 to complete the accepted active-fleet v3 migration and retire the legacy v2 plane before resuming broad semantic-execution implementation work. Continue to treat PR #590 as the umbrella program and preserve its architecture/benchmark state, but do not let the legacy runner substrate remain a reliability dependency underneath new orchestration work. Consume only durable GitRunner results; do not issue canary/cutover authority from this task. After v3 production cutover and v2 retirement are accepted, resume the resumable-reasoning benchmark, architecture review, unseen-workflow extension proof, and minimal implementation freeze.

## Remaining work

- Track the separate GitRunner task as the current P0 infrastructure dependency until accepted v3 production cutover and v2 retirement are complete; do not issue its live authority from this umbrella task.
- After the GitRunner substrate is stable on v3, implement and run the resumable-reasoning benchmark pilot.
- Compare frontier long-horizon, Instant persistent-chat, Instant stateless-resume, Instant decomposition/critic, and hybrid-escalation arms using objective validators and usage/context metrics.
- Run an independent architecture review of the preferred hybrid semantic-projection hypothesis.
- Prove one previously unseen workflow/domain extension without kernel changes or authority leakage.
- Decide whether Temporal/Dapr or LangGraph/Agent Framework spikes are justified by expected material benefit.
- Freeze and implement the smallest viable semantic projection + ReasoningProcess + executor/resource router only after evidence is sufficient.
- Migrate representative workflows across research, engineering, data science, papers, presentations, tutoring, documents, and controller/runtime operations.
- Measure and minimize scarce frontier allowance; keep escalation evidence-based.

## Blockers / gates

- Architecture freeze is intentionally blocked pending resumable-reasoning benchmark evidence and independent review.
- Live GitRunner migration actions remain controlled by workspace-github-actions-control-plane-protocol-redesign-v1 and require fresh class-specific authority; this task cannot issue that authority.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
