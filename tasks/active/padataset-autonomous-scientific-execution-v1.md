<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-autonomous-scientific-execution-v1
- Title: PADataset autonomous scientific execution v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Make PADataset scientific GPU experiments autonomously executable by ChatGPT through the existing self-hosted Lambda control plane using an exact root-owned DNNs runtime, exact PR-head provenance, read-only project data/cache authority, bounded experiment request schemas, durable artifacts/receipts, and no per-run operator terminal work.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: padataset-autonomous-scientific-execution-v1
- Remote checkpoint: 3133fe46f9f30bc77637226dc24c5e796a7fe71b
- Remote verified: false

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d27eb8feb481696548766b8df325737d766a8d3a
- Remote verified: true

## Next safe action

Create a fresh PR from workspace-control branch padataset-autonomous-scientific-execution-v1 (implementation checkpoint 3133fe46f9f30bc77637226dc24c5e796a7fe71b plus handoff-only state commits) to current main 517911090acd316fd47190b0db0a36c4d81b589e. First require normal Workspace Control Validation PASS; then trigger exactly one authoritative /workspace-control-validate for that immutable PR head. Do not perform live host activation before both gates pass.

## Remaining work

- Open a fresh Workspace Control Stage-5 PR from padataset-autonomous-scientific-execution-v1 to current main 517911090acd316fd47190b0db0a36c4d81b589e.
- Run normal Workspace Control Validation on the exact PR head. Diagnose/fix only evidence-backed failures; do not broaden authority or alter live host state.
- After normal PASS, issue exactly one /workspace-control-validate <exact-head-sha> request and require authoritative self-hosted PASS on the identical immutable SHA.
- Promote the validated Stage-5 policy to main, then design and validate the additive v3 live-activation transaction for the new dedicated scientific class/route without replaying the original v2→v3 cutover.
- Apply the reviewed live activation, verify the dedicated controller/scale set and exact compiled runtime/data bindings, then run autonomous scientific smoke, bounded training smoke, full PA2 Stage03 backbone training, and Architecture C evaluation.
- Refresh Workspace Shell trusted task authority to include padataset-autonomous-scientific-execution-v1 once the final promoted/activated state is durable.
- Track the separate v3 controller primary-rate-limit 403 handling defect under separately authorized infrastructure scope; do not mix that hotfix into this scientific task.

## Blockers / gates

- Stage-5 v3 policy implementation is constructed on branch padataset-autonomous-scientific-execution-v1 but has not yet passed repository validation.
- The branch has no current pull request after PR #613 was merged; a fresh Stage-5 PR to main is required to obtain the normal pull_request validation gate.
- No live host activation has been attempted for the dedicated scientific class. The deployment overlay intentionally leaves padataset-scientific-single-gpu-v1 NOT_INSTALLED/INACTIVE and padataset:scientific-single-gpu DISABLED.
- Live Workspace Shell trusted authority still does not include padataset-autonomous-scientific-execution-v1; refresh it only after the final Stage-5 policy is validated/promoted and the live activation transaction is accepted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
