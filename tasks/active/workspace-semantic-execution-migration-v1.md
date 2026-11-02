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

## Current stage

architecture_family_comparison_and_benchmark_design

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

## Durable architecture artifacts

- architecture/workspace-semantic-execution-migration.v0.1.md
- architecture/workspace-capability-workflow-inventory.v0.1.md
- architecture/workspace-semantic-execution-architecture-options.v0.1.md

## Current architecture status

Hybrid semantic projection + existing execution substrates is the current **preferred migration hypothesis**, not a frozen decision.

The task explicitly compares:

- minimal evolution of current Workspace Control;
- generalized research-engine durable kernel;
- graph-first semantic execution;
- Temporal/Dapr durable-workflow substrate;
- LangGraph/Microsoft Agent Framework-style cognitive workflow runtime;
- hybrid semantic projection + current task/GitRunner/Workspace Shell/research-engine substrates.

No external framework or graph database is authorized for production adoption merely because it overlaps conceptually.

## Resumable reasoning hypothesis

Long-horizon cognitive work should be representable as durable reasoning state advanced by disposable bounded model invocations.

Required distinction:

```text
TOO_LARGE
→ decompose
→ retry cheaper executor

INTRINSICALLY_DIFFICULT
→ escalate reasoning tier
```

Repeated continuation is not assumed to turn a weaker model into a stronger model. This must be benchmarked.

## GitRunner dependency

Separate authoritative task:

`workspace-github-actions-control-plane-protocol-redesign-v1`

Current branch evidence:

`workspace-control@github-actions-control-plane-protocol-redesign-v1:6456847b0b4b1268ed6f5bd4d0b847ebde1a21e5`

Current migration facts:

- first v3 `workspace-control-control-small-v1` canary already accepted;
- next class is `padataset-cpu-public-v1`;
- then `padataset-gpu-single-public-v1`;
- `research-cpu-public-v1` remains separately gated;
- all Research GPU-derived classes remain NO_BY_DEFAULT.

Workspace Shell dependency is satisfied by durable PR #573 acceptance comment `6565110368`:

- Workspace Shell task COMPLETE;
- durable head `44b4e4f2020450c81cec56e86b711cdee7e651d9`;
- accepted execution/authority SHA `01a95b61410e2f427b9885a19e6a0b9c5ee60a38`;
- Workspace Control Validation run `41359338969` SUCCESS.

This task MUST NOT reuse Workspace Shell authority or manufacture the fresh GitRunner one-shot authority required for PADataset.

## Validation state

- PR #590 initial hosted Workspace Control Validation run `41378088808`: SUCCESS.
- Current Lambda controller validation request:
  `/workspace-control-validate cbc71b51b28c96b7b08b92a5e8e17b8566803d73`
- Lambda CI Workspace Control Validation run `41378944347` was observed queued and is treated as an external async wait.

## Next safe action

Continue evidence-first architecture work on PR #590: create the resumable reasoning benchmark contract and minimal semantic-core/executor-resource schemas, while treating the Lambda validation run as an external async wait.

Do not perform live GitRunner canary/migration mutation from this task. Consume the separate GitRunner task's durable results when they change.

## Remaining work

- Observe exact-head Lambda validation result only when state changes; do not burn reasoning cycles polling.
- Define and implement the resumable Instant-vs-frontier benchmark contract on disposable benchmark state.
- Define the minimal semantic core and versioned domain-extension registration contract.
- Define executor/resource/quota ontology and routing/escalation decision contract.
- Expand workflow inventory to concrete workflow descriptors and acceptance cases.
- Run an independent architecture review of the hybrid hypothesis.
- Perform a bounded external-runtime spike only if comparison evidence justifies it.
- Demonstrate an unseen workflow extension without kernel change.
- Keep the separate GitRunner migration progressing under its own authority, beginning with PADataset CPU when fresh canary authority exists.

## Blockers / gates

- Architecture freeze is intentionally blocked pending resumable-reasoning benchmark evidence and independent review.
- Live GitRunner migration actions remain controlled by workspace-github-actions-control-plane-protocol-redesign-v1 and require fresh class-specific authority.

## Fresh-chat initialization

@GitHub
@Heartbeat
@Workspace Shell

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, PR #590, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
Do not inherit or invent live GitRunner canary authority from this task.
