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
- Remote checkpoint: 48c5fcfa5b0a7312b6d944819c559858cb41a3a0
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

D4 V1.10 EXPLICIT ONE-SHOT APPROVAL GATE. v1.9 is consumed and non-reusable. Root cause is validated and repaired backend-only: .NET PostAsJsonAsync chunked request bodies versus the former Content-Length-only backend reader. Repair 020d35156d90e8268fb560a10e67098a146880de passed Workspace #3132 / Semantic #434 / Operator #705; frozen v1.10 review 0d74dc4b7562faef60e9e8c1b9748691ec596963 passed #3133/#435/#706; cleanup-gate bookkeeping 48c5fcfa5b0a7312b6d944819c559858cb41a3a0 passed #3134/#436/#707. Windows cleanup is accepted because wop-down emitted WORKSPACE_OPERATOR_DEV_OFFLINE=PASS and wop-status emitted WORKSPACE_OPERATOR_DEV_STATUS=OFFLINE, and the harness explicitly emits only DEV_OFFLINE when runtime.json is already absent. Accepted A7 bytes remain unchanged. ZERO live authority exists. Stop until Adam freshly and explicitly approves exactly one v1.10 D4 attempt. After approval only, create a fresh v1.10 one-shot authority bound to the validated repair/review/source, exact-head validate it, then execute one bounded live attempt. No silent retry.

## Remaining work

- Wait for Adam's fresh explicit approval of exactly one v1.10 D4 attempt.
- After approval only, create and exact-head validate a fresh one-shot v1.10 authority bound to the validated chunked-POST backend repair and unchanged A7 frontend.
- Execute exactly one bounded v1.10 D4 attempt.
- After D4 PASS, proceed to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- LIVE AUTHORITY: v1.10 repair/review and Windows cleanup are accepted, but the review grants zero live authority. Fresh explicit approval for exactly one v1.10 D4 attempt is required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
