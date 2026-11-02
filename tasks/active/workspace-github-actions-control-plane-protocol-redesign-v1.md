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
- Remote checkpoint: 8b5afb6a77ae3347300904c4e410a8ce5ede1ecd
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d214b20471aac348bd28802596b92f81ee146b76
- Remote verified: true

## Next safe action

PADataset GPU canary workflow is now trusted on main and the bounded GPU live operator is validated. The next action requires the live Lambda privileged transaction boundary: run exactly `scripts/lambda_ci_v3_padataset_gpu_canary_live.sh` from clean workspace-control head 8b5afb6a77ae3347300904c4e410a8ce5ede1ecd. The operator must first prove all v3 classes inactive/non-restarting, retry-history for the GPU target, exact controller/helper bindings, exact main workflow blob 9311657f079aa1894d16d5e83ed0b18a813af487, and target repository `https://github.com/adamtrott78/PADataset`; only then may it mint one fresh ACTIVATE_ONE_V3_CANARY authority and dispatch exactly `padataset-gpu-single-public-v1`. Do not repeat workspace-control or PADataset CPU canaries.

## Remaining work

- Execute the validated bounded GPU operator once from exact clean workspace-control head 8b5afb6a77ae3347300904c4e410a8ce5ede1ecd.
- Independently verify the resulting PADataset workflow run/job and immutable-envelope step, and require terminal V3_CANARY_ROLLBACK=PASS / GENERATION_EXCLUSION_ROLLBACK=PASS / PADATASET_GPU_CANARY_ACCEPTED=PASS.
- Attest roots, all v3 class inactivity/non-restart residue as permitted, zero v3 transient/resource residue, exact v2 restoration, PADataset CPU/GPU lane health, and Research GPU containment.
- Record PADataset GPU acceptance durably, then execute controlled production v3 cutover and v2 retirement.
- Resume workspace-semantic-execution-migration-v1 after the v3 production migration boundary is accepted.

## Blockers / gates

- Live GPU canary execution requires the existing root/sudo transaction boundary on Lambda; Workspace Shell has no reviewed privileged helper authorizing this transaction.
- No GPU canary is accepted until its fresh one-shot authority, workflow run, immutable-envelope success, terminal rollback, and independent poststate attestations all pass.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.
- Production v3 cutover/v2 retirement remains gated on accepted PADataset GPU canary plus exact post-canary validation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
