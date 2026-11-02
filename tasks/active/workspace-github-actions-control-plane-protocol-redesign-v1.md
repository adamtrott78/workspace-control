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
- Remote checkpoint: 56e5976597b0d1523ead6a11cdfe6f8a9d23dda0
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

Repository and observation preflights for PADataset GPU attempt #2 are now prepared and validated at implementation head 56e5976597b0d1523ead6a11cdfe6f8a9d23dda0 / Validation 41424882222 SUCCESS. From a clean checkout of the current durable GitRunner branch after this task-sync head validates, execute exactly scripts/lambda_ci_v3_padataset_gpu_canary_live.sh through the existing operator/root transaction boundary. The script must independently re-prove roots healthy, all nine v3 class controllers inactive/non-restarting and boot-disabled, exact e1a2d44 runtime override/update-receipt binding, retry history, zero active prior canary runs, exact PADataset main workflow blob 9311657f079aa1894d16d5e83ed0b18a813af487, and drained legacy scale sets BEFORE it creates one NEW ACTIVATE_ONE_V3_CANARY authority for exactly padataset-gpu-single-public-v1. Do not reuse GPU #1 authority and do not repeat accepted canaries.

## Remaining work

- Execute exactly one fresh-authority padataset-gpu-single-public-v1 canary through the validated operator/root transaction boundary; observe immutable-envelope success and terminal rollback.
- Independently verify the resulting PADataset workflow run/job and require V3_CANARY_ROLLBACK=PASS, GENERATION_EXCLUSION_ROLLBACK=PASS, POST_CANARY_ROOT_SERVICES=ACTIVE, POST_CANARY_V3_CLASS_CONTROLLERS=INACTIVE, RESEARCH_GPU_CONTAINMENT=PRESERVED, CANARY_RESULT=SUCCESS, and PADATASET_GPU_CANARY_ACCEPTED=PASS.
- Independently attest roots, no v3 transient/resource residue, exact v2 restoration, PADataset lane health, and Research GPU containment; record GPU acceptance durably.
- Then perform the single controlled production generation cutover, drain/quiesce v2, retarget accepted workflows to exact v3 scale-set names, activate accepted production v3 classes, validate production, move v2 DRAINING -> RETIRED while preserving rollback bytes/state, and later clean legacy state.
- Immediately resume workspace-semantic-execution-migration-v1 umbrella work after the v3/v2 infrastructure gate is accepted.

## Blockers / gates

- GPU canary remains unaccepted; failed run 41420426352 is historical and its consumed authority must never be reused.
- The repository-side GPU #2 operator is validated, but actual canary activation remains a live root/sudo transaction boundary. Current Workspace Shell authority cannot mint operator approvals or generic root execution, and the accepted Workspace Shell task explicitly keeps privileged helper/trust stores fail-closed.
- The next GPU attempt requires a completely fresh one-shot ACTIVATE_ONE_V3_CANARY authority created only by the validated operator after its live preflights pass.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.
- Production v3 cutover/v2 retirement remains gated on accepted PADataset GPU canary and exact post-canary acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
