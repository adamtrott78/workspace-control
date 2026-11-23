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
- Remote checkpoint: 9f21d300efc9a82db358bd636b53f51e73a47946
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

D4 V1.13 EXPLICIT ONE-SHOT APPROVAL GATE. v1.12 aborted pre-consumption after STAGE12_CANDIDATE_BASELINE=PASS because an exact stale Stage12 Tailscale route was still present; semantic live binding and the live consumption marker were never reached, so v1.12 is superseded/non-reusable but unconsumed. v1.13 fixes the preflight ordering and normalizes only the exact /operator-bridge/v1 -> 127.0.0.1:8765/operator-bridge/v1 route, and only after proving port 8765 has no listener; arbitrary Serve/Funnel drift still fails closed. Candidate head 534ff64254643346551a9d17a402f8cc4ff84b07 passed Workspace #3148 / Semantic #450 / Operator #721. Frozen v1.13 review head 9f21d300efc9a82db358bd636b53f51e73a47946 passed Workspace #3149 / Semantic #451 / Operator #722. Candidate baseline 7bab6ff5…, semantic repair 020d35156… / backend blob 3b6893c1…, and A7 remain unchanged. ZERO v1.13 live authority exists. Stop until Adam freshly and explicitly approves exactly one v1.13 D4 attempt. After approval only, create and exact-head validate one fresh authority; require candidate baseline PASS, exact stale-route normalization/clean root state, and STAGE12_SEMANTIC_LIVE_BINDING=PASS before consumption.

## Remaining work

- Wait for Adam's fresh explicit approval of exactly one v1.13 D4 attempt.
- After approval only, create and exact-head validate a fresh one-shot v1.13 authority bound to the exact stale-route normalization, candidate baseline 7bab6ff5…, semantic repair 020d35156… / backend blob 3b6893c1…, and unchanged A7.
- Execute exactly one bounded v1.13 D4 attempt. STAGE12_CANDIDATE_BASELINE=PASS, any required TAILSCALE_STALE_STAGE12_ROUTE_CLEARED=PASS, TAILSCALE_STAGE12_ROUTE_ABSENT=PASS, and STAGE12_SEMANTIC_LIVE_BINDING=PASS must occur before STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS.
- After D4 PASS, proceed to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- LIVE AUTHORITY: v1.13 repair and frozen review are exact-head validated, but zero live authority exists. Fresh explicit approval for exactly one v1.13 D4 attempt is required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-semantic-execution-migration-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
