<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 90f9a429fb393f0e4dd1c0be8263f54371b48a20
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

PADATASET CPU CANARY DEFAULT-BRANCH GATE SATISFIED. adamtrott78/PADataset PR #3 was explicitly authorized by the operator and merged with expected head dfc739e1ed275cf4bff3a5f3038ff1089b3bd739 via squash merge commit 12d8ad19d14f2ab42474e159f958060f3050cf1e. PADataset main now contains exact workflow blob f42c165ef6dc658f026976984c87d2eb28f5cd17 at `.github/workflows/workspace-ci-v3-migration-canary-padataset-cpu-public-v1.yml`; no workflow drift occurred. Root recovery remains accepted and must not be repeated. Dedicated live operator `scripts/lambda_ci_v3_padataset_cpu_canary_live.sh` remains validated at head 97cb93f3b46adea0a710717caeb84ef7999f6fcd / Validation 41411615725 and is present unchanged in durable task head 90f9a429fb393f0e4dd1c0be8263f54371b48a20 / Validation 41411798734. The operator binds controller/canary provenance to accepted source 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa, exact transaction helper blob 0c02ca17cf267f1c3986bfee75ebfc6172ca592a, exact PADataset main workflow blob f42c165e..., PADataset-scoped credentials, and a fresh ACTIVATE_ONE_V3_CANARY authority created only after preflights. Next safe action is the operator-root invocation of that exact bounded PADataset CPU canary script; Workspace Shell cannot perform it because the privileged-helper approval registry has no accepted helper/signature for this transaction.

## Remaining work

- Run `scripts/lambda_ci_v3_padataset_cpu_canary_live.sh` once from an exact clean checkout of validated durable head 90f9a429fb393f0e4dd1c0be8263f54371b48a20. The script preflights current live state, verifies exact PADataset main blob f42c165e..., creates one fresh ACTIVATE_ONE_V3_CANARY authority, quiesces all v2 controllers under generation exclusion, activates only padataset-cpu-public-v1, dispatches the owner-only canary, waits terminal, then rolls back to exact v2 prestate.
- After the operator returns, independently attest root services, every v3 class inactive, zero v3 resource/transient residue, exact v2 controller restoration, and Research GPU containment via Workspace Shell/maintenance receipts; record the canary run/transaction evidence.
- Then stage/authorize/execute padataset-gpu-single-public-v1 under a separate fresh authority.
- After PADataset CPU+GPU acceptance, execute controlled production v3 cutover and v2 retirement, then resume workspace-semantic-execution-migration-v1 umbrella work.

## Blockers / gates

- The exact PADataset CPU canary is now repository-ready. The only immediate blocker is operator-root execution of the reviewed live canary script because Workspace Shell cannot mint or transport an unconfigured privileged-helper approval.
- The live operator will create one fresh exact-bound ACTIVATE_ONE_V3_CANARY authority only after all preflights; no prior root/canary authority may be reused.
- Research CPU remains separately gated; all Research GPU-derived v3 classes remain inherited-contained and NO_BY_DEFAULT; Research Engine PR #283 remains proposal-only.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
