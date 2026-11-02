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
- Remote checkpoint: 97cb93f3b46adea0a710717caeb84ef7999f6fcd
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

PADATASET CPU CANARY STAGED; DEFAULT-BRANCH PLACEMENT IS THE NEXT AUTHORITY GATE. Root recovery is accepted and must not be repeated. Exact PADataset CPU migration workflow is staged as draft PR adamtrott78/PADataset#3, head dfc739e1ed275cf4bff3a5f3038ff1089b3bd739, single changed file `.github/workflows/workspace-ci-v3-migration-canary-padataset-cpu-public-v1.yml`, exact generated blob f42c165ef6dc658f026976984c87d2eb28f5cd17. The workflow is workflow_dispatch-only, owner-gated to adamtrott78, performs no checkout/candidate execution, and invokes only the immutable root-installed canary probe for padataset-cpu-public-v1. Dedicated live operator scripts/lambda_ci_v3_padataset_cpu_canary_live.sh at head 97cb93f3b46adea0a710717caeb84ef7999f6fcd passed Workspace Control Validation 41411615725 SUCCESS. It deliberately separates mutable operator HEAD from accepted controller/canary generation 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa, binds transaction helper blob 0c02ca17cf267f1c3986bfee75ebfc6172ca592a, requires exact PADataset main workflow blob f42c165e..., uses repository-scoped ci-gh-padataset credentials, verifies effective installed generation before mutation, and creates a fresh ACTIVATE_ONE_V3_CANARY authority only after all preflights. Do not dispatch or consume canary authority until PR #3 exact workflow blob is on PADataset main. Landing that exact proposal onto the owning default branch is the next operator/authority decision.

## Remaining work

- Land only the exact PADataset PR #3 workflow blob f42c165ef6dc658f026976984c87d2eb28f5cd17 on PADataset main through an authorized repository decision; do not alter the workflow while landing it.
- After main attests that exact blob, run the validated PADataset CPU live operator from an exact clean checkout of the then-current validated workspace-control task head. The operator binds canary generation/controller provenance to accepted source 3e8a231483413ba3a16d405ba61b55d0ab9ff3aa, creates a fresh one-shot ACTIVATE_ONE_V3_CANARY authority only after preflight, runs/observes the canary, and rolls generation exclusion back to exact v2 prestate.
- Independently attest root services, all v3 class inactivity, zero resource/transient residue, exact v2 restoration, and Research GPU containment after the CPU canary.
- Then stage/authorize/execute padataset-gpu-single-public-v1 under a separate fresh authority.
- After PADataset CPU+GPU acceptance, execute controlled production v3 cutover and v2 retirement, then resume workspace-semantic-execution-migration-v1 umbrella work.

## Blockers / gates

- adamtrott78/PADataset main does not yet contain the exact padataset-cpu-public-v1 migration workflow. Draft PR #3 stages the exact generated blob f42c165ef6dc658f026976984c87d2eb28f5cd17; default-branch placement is a repository-authority gate and has not been inferred or performed.
- After exact default-branch placement, live padataset-cpu-public-v1 still requires one fresh ACTIVATE_ONE_V3_CANARY authority created by the validated operator; no prior root/canary authority may be reused.
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
