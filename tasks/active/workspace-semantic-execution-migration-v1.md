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
- Remote checkpoint: 0d74dc4b7562faef60e9e8c1b9748691ec596963
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

D4 V1.10 WINDOWS CLEANUP GATE. v1.9 is consumed and non-reusable after Q1 proved repeated Ctrl+Space dispatches failed before actionId with HttpRequestException. Root cause is now validated: .NET PostAsJsonAsync sends chunked JSON while the backend accepted only Content-Length; backend-only repair 020d35156d90e8268fb560a10e67098a146880de passed Workspace #3132 / Semantic #434 / Operator #705, and frozen v1.10 review head 0d74dc4b7562faef60e9e8c1b9748691ec596963 passed Workspace #3133 / Semantic #435 / Operator #706. Accepted A7 bytes remain unchanged and v1.10 grants ZERO live authority. Next prove the consumed v1.9 Windows runtime is clean/OFFLINE using the accepted wop-down + wop-status path. After cleanup only, fresh explicit approval is required for exactly one v1.10 attempt; no silent retry.

## Remaining work

- Prove consumed v1.9 Windows cleanup with WORKSPACE_OPERATOR_RUNTIME_PROCESS_CLEANUP=PASS, WORKSPACE_OPERATOR_RUNTIME_WORKDIR_CLEANUP=PASS, WORKSPACE_OPERATOR_DEV_OFFLINE=PASS, and WORKSPACE_OPERATOR_DEV_STATUS=OFFLINE.
- After cleanup, obtain fresh explicit approval for exactly one v1.10 D4 attempt.
- After approval only, create and exact-head validate a fresh one-shot v1.10 authority bound to the validated chunked-POST backend repair and unchanged A7 frontend.
- Execute exactly one bounded v1.10 D4 attempt; after D4 PASS proceed to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- V1.9 WINDOWS CLEANUP: the consumed v1.9 attempt is non-reusable; exact accepted Windows cleanup/OFFLINE evidence is required before any v1.10 approval/authority.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
