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

Treat this as the umbrella program. In a fresh ChatGPT conversation, first finish the bounded GitRunner incident diagnosis through the live PR #591 Workspace Shell observability surface (new unit_logs_redacted + maintenance_receipt operations) and persist the exact root cause/repair evidence to the GitRunner task/PR #572. Do not let that incident consume or replace the broader migration. Once lane serviceability is understood, continue the semantic-execution program on PR #590 by implementing/running the resumable Instant-vs-frontier benchmark pilot, independently reviewing the hybrid architecture hypothesis, proving an unseen workflow extension without kernel change, and only then freezing implementation architecture. Keep PADataset/Research v3 canary authority owned exclusively by the GitRunner task.

## Remaining work

- Fresh-chat GitRunner incident diagnosis: use PR #591 live unit_logs_redacted and maintenance_receipt operations to identify why an ACTIVE legacy workspace-control controller is not assigning queued run 41378944347; record exact evidence and repair without widening authority gratuitously.
- Keep the GitRunner v3 fleet migration as a separate authority-owned dependency: after incident/serviceability proof, PADataset CPU is next under a fresh class-specific one-shot canary authority, then PADataset GPU; Research CPU remains separately gated and all Research GPU-derived classes remain NO_BY_DEFAULT.
- Implement and run a small resumable-reasoning benchmark pilot using the durable contract at benchmarks/workspace-semantic-execution/resumable_reasoning_v1.json.
- Compare frontier long-horizon, Instant persistent-chat, Instant stateless-resume, Instant decomposition/critic, and hybrid-escalation arms using objective validators and usage/context metrics.
- Run an independent architecture review of the preferred hybrid semantic-projection hypothesis; do not freeze merely because the current design is coherent.
- Prove the semantic core can register and execute one previously unseen workflow/domain extension without a kernel domain switch and without authority leakage.
- Decide whether a Temporal/Dapr or LangGraph/Agent Framework spike is justified by expected material benefit; benchmark before adopting.
- After architecture evidence is sufficient, implement the minimal semantic projection + ReasoningProcess + executor/resource router incrementally while preserving current project-local authority and execution substrates.
- Migrate representative workflows across research/experiments, coding+CI repair, architecture review, data science, paper creation, presentations, tutoring/homework, documents, and controller/runtime operations.
- Measure and minimize scarce frontier allowance rather than assuming Instant is equivalent to frontier reasoning; escalation must be evidence-based.

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
