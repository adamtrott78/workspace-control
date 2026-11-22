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

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-semantic-execution-migration-v1
- Remote checkpoint: 3986cbcb547e71c99c008cc22aad463df8165954
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

D4 V1.9 REVIEW / CLEANUP GATE. v1.8 is consumed and non-reusable after a real Q1 remote-dispatch failure; do not rerun it. v1.9 orchestration candidate 3986cbcb547e71c99c008cc22aad463df8165954 is 3/3 green (#3125/#425/#698) and preserves the frozen A7 frontend exactly. Immediate operator-only action is `wop-down` then `wop-status` to clean the degraded v1.8 Windows runtime and require OFFLINE. This v1.9 review grants zero live authority. After cleanup evidence, freeze/validate the v1.9 review state and request fresh explicit one-shot approval before any live retry.

## Remaining work

- Record Windows v1.8 cleanup PASS/OFFLINE evidence.
- Validate/freeze D4 v1.9 review/procedure exact head with A7 bytes unchanged.
- Only after explicit approval, create and validate a fresh one-shot v1.9 authority.
- After D4 PASS, continue to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- WINDOWS CLEANUP: current v1.8 helper runtime was observed DEGRADED (helper alive, web-ext/Firefox absent) and must be cleaned with accepted wop-down, then wop-status OFFLINE.
- LIVE AUTHORITY: v1.8 is consumed/non-reusable. v1.9 review candidate grants zero live authority; fresh exact-head validation and explicit one-shot approval are required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
