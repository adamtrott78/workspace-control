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
- Remote checkpoint: c0108f87f9dd10a517151ab399762530f06610cf
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

Continue evidence-first architecture work on PR #590: create the resumable reasoning benchmark contract and minimal semantic-core/executor-resource schemas, while treating the Lambda validation run as an external async wait. Do not perform live GitRunner canary/migration mutation from this task. Consume the separate GitRunner task's durable results when they change.

## Remaining work

- Observe exact-head Lambda validation result without polling with a reasoning model while nothing changes.
- Define and implement the resumable Instant-vs-frontier benchmark contract on disposable benchmark state.
- Define the minimal semantic core and versioned domain-extension registration contract.
- Define executor/resource/quota ontology and routing/escalation decision contract.
- Expand workflow inventory to concrete workflow descriptors and acceptance cases.
- Run an independent architecture review of the hybrid hypothesis.
- Perform a bounded external-runtime spike only if the comparison shows sufficient likely benefit.
- Demonstrate an unseen workflow extension without kernel change.
- Keep the separate GitRunner migration progressing under its own authority, starting with PADataset CPU when fresh canary authority exists.

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
