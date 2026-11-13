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
- Remote checkpoint: c24fda155bb5735aab5b34e7a4b3e68e46c0adbc
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

Design and implement the first end-to-end external cognitive + execution slice using architecture/workspace-semantic-execution-cognitive-execution-state-architecture.v0.1.md and architecture/workspace-semantic-execution-state-store-contract.v0.1.json. The slice must include: append-only EventRecord history, relational/current WorkItem + ReasoningProcess + lease/generation state, typed dependency DAG edges, DecisionRecord, CandidateAction -> ActionSpec trust boundary, EffectReceipt + postcondition validation, and a rebuildable semantic projection used by the packet compiler. Use one real user workflow as the proving workload. Do not choose a graph database/vector database/general workflow engine before measured need. Re-review the architecture after the first end-to-end reasoning+execution workflow instead of treating v0.1 as final.

## Remaining work

- COGNITIVE + EXECUTION SYSTEM: implement reasoning and execution as separate coupled loops. Reasoning produces findings/decisions/plans/CandidateActions; deterministic action compilation binds exact target, authority, preconditions, idempotency, expected effects, validator, retry and compensation before execution.
- FIT-FOR-PURPOSE STATE: implement the state ownership contract with append-only process history, relational current state, typed work DAG, first-class DecisionRecords, immutable artifact/evidence refs, rebuildable semantic graph projection, and non-authoritative retrieval/session caches.
- EXECUTION PRECISION: require effect receipts and postcondition validation. Successful tool invocation alone is insufficient for COMPLETE; retries must be classified and stale/duplicate effects fenced.
- EVOLUTIONARY ARCHITECTURE: trigger explicit architecture review after the first real end-to-end workflow, after three representative domain workflows, after first material concurrency/compensation incidents, before introducing new graph/vector/workflow substrates, and before production promotion.
- ACCELERATED BACKEND LANE: implement the deterministic orchestration kernel from workspace-semantic-execution-orchestrator-implementation-plan.v0.1.md Phase 1: WorkItem/ReasoningProcess/Attempt/Lease/Event/WaitCondition/RoutingDecision/ExecutorSession/ValidationResult plus CAS/generation fencing, stale-worker rejection, idempotent transitions, event-driven waits, and fail-closed unknown transitions.
- ACCELERATED BACKEND LANE: implement executable task-tree decomposition semantics and recursive TOO_LARGE -> DECOMPOSE behavior, preserving inherited constraints, provenance, validator contracts, authority refs, and dependency edges.
- ACCELERATED BACKEND LANE: implement the executor registry/resource router, semantic packet compiler, persistent session broker, and validator/event service so disposable Instant workers can process bounded leaves and publish durable results.
- ACCELERATED BACKEND LANE: replay the already-proven multi-worker queue/CAS/lease-recovery fixtures through the new kernel, then add one end-to-end decomposed workflow where multiple Instant-worker leaves complete independently and a synthesizer consumes validated outputs.
- PARALLEL CALIBRATION LANE: finish remaining Operator Bridge Stage-10 UX trials only as required for real-account/production promotion; do not serialize backend development behind them.
- PARALLEL CLAIM-BEARING BENCHMARK LANE: provision evaluator-only hidden runtime storage and run replicated capability scoring before making strong Instant-vs-frontier equivalence claims.
- Close Workspace Shell recovery-plane lifecycle gaps discovered by the power outage: persistent tmpfiles/boot recovery and a narrow standing/reviewed-helper authority model that removes routine operator sudo relay without exposing generic root shell or allowing model reasoning to mint authority.
- Explicitly determine whether repeated durable Instant reasoning quanta can match frontier long-horizon effectiveness for iterative research/design/test/evaluate loops; separate TOO_LARGE/decompose-again from INTRINSICALLY_DIFFICULT/escalate.
- Run an independent architecture review of the preferred hybrid semantic-projection hypothesis and challenge whether a different execution substrate/agent/workflow framework materially improves reliability or allowance efficiency.
- Freeze and implement the smallest stable semantic core, versioned domain/workflow extension contract, durable ReasoningProcess, executor/provider/model/surface/harness capability model, resource/quota router, task-tree/lease/CAS semantics, and evidence-based escalation policy.
- Operator UX design UX-00 through UX-13 is frozen and child implementation authority is established. Continue workspace-operator-bridge-implementation-v1 through its staged implementation, fake-worker validation, UX-09/UX-11 empirical gates, and bounded real-account calibration before any production promotion.
- Migrate representative workflows incrementally across: automated research/evaluate/iterate loops; systems engineering and coding; data science/ML experiments; PADataset/research-engine; paper drafting/evidence/citation pipelines; slide/presentation creation; tutoring and homework/assignment generation for MTH602/EAS501/CIS560; generic document/artifact production; GitRunner/Lambda operations; Workspace Shell maintenance; and future workflows not known today.
- Preserve project-local truth, exact provenance/SHA bindings, authority firewalls, rollback, objective validators, and semantic ontology/graph extensions while minimizing scarce frontier usage.
- Measure executor effectiveness and scarce frontier allowance continuously; route DETERMINISTIC -> Instant/local -> cheaper hosted -> frontier only when capability/reasoning evidence requires escalation.

## Blockers / gates

- Architecture freeze remains blocked pending the resumable-reasoning effectiveness benchmark and independent architecture review. The previously unseen workflow/domain extension proof is now validated.
- Workspace Shell still lacks a sufficiently general but narrow standing privileged-helper authority path for routine reviewed root operations; operator terminal relay must be reduced without widening to arbitrary sudo/bash.
- Hidden-ephemeral evaluator generation and commitment verification are implemented, but the evaluator-only runtime store is not yet proven inaccessible to scored workers. Strong frontier-equivalence claims remain blocked until that storage boundary is validated.
- Claim-bearing benchmark conclusions still require evaluator-only runtime isolation and replicated scoring; this blocks strong capability-equivalence claims, not deterministic orchestrator/backend implementation.
- Remaining Operator Bridge Stage-10 UX trials gate real-account/production promotion, but they do not block implementation of the deterministic task-tree, decomposition, routing, packet-compiler, session-broker, event/wait, and validator backend.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
