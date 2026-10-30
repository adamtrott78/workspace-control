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
- Remote checkpoint: 01019177fcb46e5ab9864ea9b764b533dcf0be81
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

Repository implementation is mechanically complete through workspace-control@01019177fcb46e5ab9864ea9b764b533dcf0be81, which passed Workspace Control Validation #1337 / run 41010515483. This includes inactive substrate install, private migration/authority state roots, one-shot short-lived anti-replay canary authority, installed-manifest-bound one-shot root-services activation/rollback, deterministic owner-only canary generation, and one-class generation-exclusion/rollback. Research Engine PR #283 remains exact head 6165556086b73d2076f205f11ec7b988150f23dd with hosted CI #642 accepted. No further repository implementation is currently required. The next step requires separate explicit live authority: apply the exact inactive substrate, then use the one-shot ACTIVATE_V3_ROOT_SERVICES transaction before the first migration-order canary. Do not merge/cut over PR #283, mutate Lambda, dispatch migration canaries, or alter Research GPU containment/retry authority without the corresponding explicit authority.

## Remaining work

- Obtain separate explicit live authority before any Lambda mutation; the migration plan currently grants NONE.
- Under that authority, apply the exact inactive v3 substrate from repository boundary 01019177fcb46e5ab9864ea9b764b533dcf0be81, verify the installed manifest, sysusers/tmpfiles/systemd/config digests, private 0700 migration roots, and that all nine class controllers plus all v3 units remain inactive/disabled.
- Issue a separate short-lived one-shot ACTIVATE_V3_ROOT_SERVICES receipt bound to the exact installed manifest/source head/root-policy digest, then run the installed lambda_ci_v3_root_activation.py helper; require reconciler attestation, provisioner socket proof, Research GPU containment preservation, and zero class/transient/resource activation.
- Deploy/bind the exact owner-only workspace-control-control-small-v1 migration canary workflow/policy under the separately authorized live canary boundary, issue a one-shot ACTIVATE_ONE_V3_CANARY receipt, execute generation exclusion, dispatch only the bounded canary, and collect exact success/rollback evidence.
- Advance additional public-network classes only in the frozen migration order under separately accepted live authority; keep every Research GPU-derived class NO_BY_DEFAULT until separate containment-recovery authority.
- Keep Research Engine PR #283 proposal-only until separate default-branch producer cutover authority binds the exact reviewed workflow blobs into the controller/deployment generation.
- For the two offline Research model classes, require accepted live canaries, separate Research GPU containment-recovery authority, and separate default-branch cutover authority before production route activation; hosted producer CI #642 is already accepted.
- Only after accepted class canaries may old scale-set drain/retirement and broader production activation be separately authorized.

## Blockers / gates

- Live migration remains deliberately unauthorized: architecture/lambda-ci-v3-migration-plan.v1.json grants live_authority=NONE. Repository mechanics are implemented and validated, but no v3 substrate/root service/class controller/canary has been installed or activated on Lambda.
- All Research GPU-derived runner classes, including research-model-single-offline-v1 and research-model-dual-offline-v1, remain inherited-contained and NO_BY_DEFAULT until separate recovery/live authority explicitly consumes the legacy containment boundary.
- Research Engine PR #283 remains draft/proposal-only at exact head 6165556086b73d2076f205f11ec7b988150f23dd. Hosted CI #642 is accepted repository evidence, but the reviewed workflow blobs are not on the default branch or in production trusted-workflow evidence, and no default-branch producer cutover authority has been granted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
