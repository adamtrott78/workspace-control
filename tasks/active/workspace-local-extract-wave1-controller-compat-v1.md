<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-controller-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-controller-compat-v1
- Title: Local EXTRACT Wave 1 controller compatibility
- Status: SUSPENDED
- Capsule schema: v2

## Goal

Make the already-authorized and already-triggered Local EXTRACT Wave 1 job claimable by the existing Lambda GPU scale-set controller with the smallest fail-closed controller compatibility fix, then activate that exact controller and recover existing workflow run 39200075204 without issuing another benchmark trigger.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a895daaee6c744c569b45d44d72e2ea3d38df15d
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Resume only after one bounded HUMAN_TERMINAL root install of exact controller merge a895daaee6c744c569b45d44d72e2ea3d38df15d using unchanged scripts/bootstrap_lambda_ci_p5.sh. The user should return the exact install output; then ChatGPT must immediately follow existing run 39200075204 / job 117891019967 through GitHub. Do not issue another Wave-1 trigger.

## Remaining work

- At the genuine root-control-plane boundary, perform one bounded HUMAN_TERMINAL sudo bootstrap from exact workspace-control controller merge a895daaee6c744c569b45d44d72e2ea3d38df15d; do not use or normalize the user's dirty canonical checkout.
- Verify P5_INSTALL=PASS, exact accepted manifest/policy blobs unchanged, all three control-plane services active, and controller NRestarts/ExecMainStatus healthy.
- Resume ChatGPT/GitHub control immediately after that root install; recover existing run 39200075204 / job 117891019967 without retriggering.
- Once the existing job is claimed, mark this child COMPLETE and return ownership to workspace-local-extract-wave1-execution-v1.

## Blockers / gates

- Root-controller install gate: workspace-control exposes only .github/workflows/workspace-control-validation.yml; there is no authorized GitHub deployment workflow for replacing the root-owned Lambda controller binary. The project runner/provisioner privilege split intentionally does not permit arbitrary root code installation. One bounded HUMAN_TERMINAL sudo bootstrap of exact controller merge a895daaee6c744c569b45d44d72e2ea3d38df15d is required before the existing queued Wave-1 run can be recovered.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-controller-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
